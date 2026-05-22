from typing import List, Optional
from sqlmodel import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderItem, CartDB, CartItem, ShippingMethod
from app.core.logger import get_logger

logger = get_logger(__name__)

class OrderRepository:
    """
    Data access layer for Orders and persistent Shopping Cart management.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- CART MANAGEMENT ---
    async def get_cart(self, user_id: str) -> CartDB:
        """
        Retrieve the current state of a user's shopping cart with its items.
        Automatically creates a cart if it doesn't exist.
        """
        from sqlalchemy.orm import selectinload
        statement = select(CartDB).where(CartDB.user_id == user_id).options(selectinload(CartDB.items))
        result = await self.session.execute(statement)
        cart = result.scalars().first()
        
        if not cart:
            cart = CartDB(user_id=user_id, items=[], total=0.0, itemsCount=0)
            self.session.add(cart)
            await self.session.commit()
            await self.session.refresh(cart, ["items"])
            
        return cart

    async def add_item_to_cart(self, user_id: str, item_data: dict) -> CartItem:
        """
        Atomically add a single item to the cart.
        """
        item = CartItem(cart_id=user_id, **item_data)
        self.session.add(item)
        await self.session.commit()
        return item

    async def remove_item_from_cart(self, user_id: str, cart_item_id: str) -> bool:
        """
        Atomically remove a specific item from the cart.
        """
        from sqlalchemy import and_
        statement = delete(CartItem).where(
            and_(CartItem.id == cart_item_id, CartItem.cart_id == user_id)
        )
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount > 0

    async def update_cart_item(self, user_id: str, cart_item_id: str, updates: dict) -> Optional[CartItem]:
        """
        Update quantity or customizations of a specific item.
        """
        statement = select(CartItem).where(
            CartItem.id == cart_item_id, 
            CartItem.cart_id == user_id
        )
        result = await self.session.execute(statement)
        item = result.scalars().first()
        
        if item:
            for key, value in updates.items():
                setattr(item, key, value)
            self.session.add(item)
            await self.session.commit()
            await self.session.refresh(item)
            
        return item

    async def update_cart_totals(self, user_id: str, total: float, count: int):
        """
        Update the summary fields of the cart.
        """
        cart = await self.session.get(CartDB, user_id)
        if cart:
            cart.total = total
            cart.itemsCount = count
            self.session.add(cart)
            await self.session.commit()

    async def clear_cart(self, user_id: str):
        """
        Atomically remove all items from a cart and reset totals.
        """
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == user_id))
        cart = await self.session.get(CartDB, user_id)
        if cart:
            cart.total = 0.0
            cart.itemsCount = 0
            self.session.add(cart)
        await self.session.commit()

    async def save_cart(self, user_id: str, cart_data: dict):
        """
        Legacy/Sync method for bulk updates. Optimized to use clear + add.
        """
        await self.clear_cart(user_id)
        
        new_items = [
            CartItem(cart_id=user_id, **item) 
            for item in cart_data.get("items", [])
        ]
        if new_items:
            self.session.add_all(new_items)
            
        cart = await self.session.get(CartDB, user_id)
        if cart:
            cart.total = cart_data.get("total", 0.0)
            cart.itemsCount = cart_data.get("itemsCount", 0)
            self.session.add(cart)
            
        await self.session.commit()

    # --- ORDER MANAGEMENT ---
    async def create_order(self, order_data: dict) -> Order:
        """
        Persist a new order record and its items in the database.
        Uses an atomic transaction (flush then commit) to ensure data integrity.
        """
        items_data = order_data.pop("items", [])
        order = Order(**order_data)
        self.session.add(order)
        
        # flush() sends the insert to the DB to generate the ID but doesn't close the transaction
        await self.session.flush() 
        
        order_items = []
        for item in items_data:
            order_items.append(OrderItem(
                order_id=order.id,
                product_id=item["productId"],
                nombre=item["nombre"],
                cantidad=item["cantidad"],
                precio=item["precio"],
                personalizaciones=item.get("personalizaciones", {}),
                subtotal=item["subtotal"]
            ))
        
        if order_items:
            self.session.add_all(order_items)
            
        # A single commit() at the end ensures everything is saved or nothing at all
        await self.session.commit()
            
        await self.session.refresh(order)
        return order

    async def list_orders_by_user(self, user_id: str) -> List[Order]:
        """
        Retrieve all orders associated with a specific user, including items.
        """
        from sqlalchemy.orm import selectinload
        statement = select(Order).where(Order.user_id == user_id).options(selectinload(Order.items))
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_all_orders(self, limit: int = 50) -> List[tuple]:
        """
        Retrieve the most recent orders joined with the User to get customer names.
        """
        from sqlalchemy.orm import selectinload
        from app.models.user import User
        from app.models.order import Order
        
        statement = (
            select(Order, User)
            .join(User, Order.user_id == User.id, isouter=True)
            .options(selectinload(Order.items))
            .order_by(Order.fecha.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.all() # Returns list of (Order, User) tuples

    async def get_analytics_summary(self) -> dict:
        """
        Perform database-level aggregations for analytics including month sales, top products,
        and weekly sales distribution.
        """
        import asyncio
        from sqlalchemy import func, extract, and_
        from datetime import datetime, timedelta
        from app.models.order import OrderItem, Order
        
        # 1. Definir periodos de tiempo precisos
        now = datetime.utcnow()
        today_date = now.date()
        yesterday_date = today_date - timedelta(days=1)
        
        start_of_week = datetime.combine(today_date - timedelta(days=6), datetime.min.time())
        start_of_prev_week = start_of_week - timedelta(days=7)
        
        # --- CONSULTAS ACTUALES ---

        # 1. Total ventas hoy (Filtrado por hoy y estado delivered)
        stmt_today = select(func.sum(Order.total)).where(
            and_(
                func.date(Order.fecha) == today_date,
                Order.status == "delivered"
            )
        )
        
        # 2. Ventas del mes actual (Solo delivered)
        stmt_month = select(func.sum(Order.total)).where(
            and_(
                extract('month', Order.fecha) == now.month,
                extract('year', Order.fecha) == now.year,
                Order.status == "delivered"
            )
        )
        
        # 3. Conteo de pedidos pendientes
        stmt_pending = select(func.count(Order.id)).where(Order.status == "pending")
        
        # 4. Productos Populares (Top 5 por cantidad vendida)
        stmt_top = (
            select(OrderItem.nombre, func.sum(OrderItem.cantidad).label("ventas"))
            .group_by(OrderItem.nombre)
            .order_by(func.sum(OrderItem.cantidad).desc())
            .limit(5)
        )

        # 5. Ventas Semanales (Últimos 7 días naturales, solo delivered)
        stmt_weekly = (
            select(func.date(Order.fecha).label("dia"), func.sum(Order.total).label("ventas"))
            .where(
                and_(
                    Order.fecha >= start_of_week,
                    Order.status == "delivered"
                )
            )
            .group_by(func.date(Order.fecha))
            .order_by(func.date(Order.fecha))
        )

        # --- CONSULTAS PARA DELTAS ---

        # 6. Ventas Ayer (para Delta Hoy)
        stmt_yesterday = select(func.sum(Order.total)).where(
            and_(
                func.date(Order.fecha) == yesterday_date,
                Order.status == "delivered"
            )
        )

        # 7. Desglose de ingresos por tipo de pago (Solo entregados)
        stmt_payments = select(
            Order.tipo_pago, 
            func.sum(Order.total).label("total")
        ).where(
            Order.status == "delivered"
        ).group_by(Order.tipo_pago)

        # 8. Pedidos e Ingresos Semana Pasada (hace 14-7 días)
        stmt_prev_week = select(
            func.count(Order.id).label("count"),
            func.sum(Order.total).label("sum")
        ).where(
            and_(
                Order.fecha >= start_of_prev_week,
                Order.fecha < start_of_week,
                Order.status == "delivered"
            )
        )

        # 8. Pedidos Semana Actual (para Delta Pedidos)
        stmt_curr_week_count = select(func.count(Order.id)).where(
            and_(
                Order.fecha >= start_of_week,
                Order.status == "delivered"
            )
        )

        # --- EJECUCIÓN SECUENCIAL (Corregida para evitar bloqueos) ---

        # Aunque asyncio.gather parezca más rápido, SQLAlchemy no soporta múltiples 
        # consultas simultáneas en la misma sesión/conexión, lo que causa latencia.
        # Gracias a los índices añadidos, la ejecución secuencial es ahora muy rápida.
        
        res_today = await self.session.execute(stmt_today)
        ventas_hoy = res_today.scalar() or 0.0

        res_month = await self.session.execute(stmt_month)
        ventas_mes = res_month.scalar() or 0.0

        res_pending = await self.session.execute(stmt_pending)
        pending_count = res_pending.scalar() or 0

        res_top = await self.session.execute(stmt_top)
        productos_populares = [
            {"nombre": row[0], "ventas": row[1]} for row in res_top.all()
        ]

        res_weekly = await self.session.execute(stmt_weekly)
        weekly_data = res_weekly.all()

        res_yesterday = await self.session.execute(stmt_yesterday)
        ventas_ayer = res_yesterday.scalar() or 0.0

        res_payments = await self.session.execute(stmt_payments)
        payment_rows = res_payments.all()
        ingresos_reales = {"efectivo": 0.0, "tarjeta": 0.0}
        for row in payment_rows:
            if row[0] in ingresos_reales:
                ingresos_reales[row[0]] = float(row[1] or 0.0)

        res_prev_week = await self.session.execute(stmt_prev_week)
        prev_week_row = res_prev_week.one()
        prev_week_count = prev_week_row[0] or 0
        prev_week_sum = prev_week_row[1] or 0.0

        res_curr_week = await self.session.execute(res_curr_week_stmt if 'res_curr_week_stmt' in locals() else stmt_curr_week_count)
        # Fix variable name if needed
        curr_week_count = res_curr_week.scalar() or 0

        # --- CÁLCULO DE DELTAS ---

        def calc_delta(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return ((curr - prev) / prev) * 100

        deltas = {
            "ventasHoy": calc_delta(ventas_hoy, ventas_ayer),
            "pedidosSemanales": calc_delta(curr_week_count, prev_week_count),
            "ingresosSemanales": calc_delta(sum(row[1] for row in weekly_data) if weekly_data else 0.0, prev_week_sum)
        }

        # --- FORMATEO SEMANAL ---

        dias_map = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
        ultimos_7_dias = {}
        for i in range(7):
            fecha = (today_date - timedelta(days=i))
            ultimos_7_dias[fecha.isoformat()] = {"day": dias_map[fecha.weekday()], "ventas": 0.0}

        for row in weekly_data:
            fecha_str = str(row[0])
            if fecha_str in ultimos_7_dias:
                ultimos_7_dias[fecha_str]["ventas"] = float(row[1] or 0.0)

        dias_orden = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        ventas_semanales = sorted(
            ultimos_7_dias.values(), 
            key=lambda x: dias_orden.index(x["day"])
        )

        return {
            "total_ventas": ventas_hoy,
            "ventas_mes": ventas_mes,
            "pending_count": pending_count,
            "productos_populares": productos_populares,
            "ventas_semanales": ventas_semanales,
            "deltas": deltas,
            "ingresos_desglosados": ingresos_reales
        }

    async def find_order_by_id(self, order_id: str) -> Optional[Order]:
        """
        Locate an order by its unique identifier, including its items.
        """
        from sqlalchemy.orm import selectinload
        statement = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def update_order_status(self, order_id: str, status: str, tracking_updates: dict = None) -> Optional[Order]:
        """
        Update the progress and status of an existing order.
        """
        order = await self.find_order_by_id(order_id)
        if order:
            order.status = status
            if tracking_updates:
                new_tracking = dict(order.tracking)
                new_tracking.update(tracking_updates)
                order.tracking = new_tracking
            self.session.add(order)
            await self.session.commit()
            return await self.find_order_by_id(order_id)
        return None

    # --- SHIPPING METHODS ---
    async def get_shipping_methods(self) -> List[ShippingMethod]:
        """List all available shipping/pickup methods."""
        statement = select(ShippingMethod).where(ShippingMethod.disponible == True)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_shipping_method(self, method_id: int) -> Optional[ShippingMethod]:
        """Get a specific shipping method by ID."""
        return await self.session.get(ShippingMethod, method_id)
