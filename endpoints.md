# ☕ The Casa Chill & Coffee - Documentación de Endpoints

Este documento detalla todos los puntos de entrada (endpoints) disponibles en la API de The Casa Chill & Coffee, organizados por capas funcionales.

---

## 🔐 CAPA DE AUTENTICACIÓN
Base URL: `/api/v1/auth`

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **POST** | `/verify` | Punto de entrada principal. Verifica token de Firebase y sincroniza el perfil local. | Body: `{idToken: string}` |
| **POST** | `/login` | Alias de `/verify` para compatibilidad con flujos de login. | Body: `{idToken: string}` |
| **POST** | `/logout` | Cierre de sesión local (principalmente gestionado en cliente). | - |

---

## 👤 CAPA DE USUARIO
Base URL: `/api/v1/user`

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **GET** | `/profile` | Obtiene el perfil completo del usuario actual. | Requiere Login |
| **PATCH** | `/profile` | Actualiza parcialmente los datos del perfil (nombre, teléfono, foto). | Body: `{nombre?, telefono?, foto?}`, Requiere Login |
| **GET** | `/addresses` | Lista todas las direcciones guardadas del usuario. | Requiere Login |
| **POST** | `/addresses` | Agrega una nueva dirección de entrega. | Body: `{calle, ciudad, codigoPostal, referencia, esDefault}`, Requiere Login |
| **DELETE** | `/addresses/{id}` | Elimina una dirección específica. | Requiere Login |
| **GET** | `/favorites` | Lista los productos marcados como favoritos. | Requiere Login |
| **POST** | `/favorites/{productId}` | Agrega un producto a la lista de favoritos. | Requiere Login |
| **DELETE** | `/favorites/{productId}` | Elimina un producto de favoritos. | Requiere Login |

---

## ☕ CAPA DE PRODUCTOS
Base URL: `/api/v1/products`

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Lista paginada de productos con filtros de categoría y búsqueda. | Query: `?category={id}&search={q}&page={1}&limit={10}` |
| **GET** | `/categories` | Lista todas las categorías disponibles. | - |
| **GET** | `/featured` | Obtiene los productos destacados/populares. | - |
| **GET** | `/search` | Búsqueda rápida de productos. | Query: `?q={termino}&page=1&limit=10` |
| **GET** | `/{product_id}` | Detalle completo de un producto (incluye ingredientes y nutrición). | - |
| **GET** | `/{product_id}/reviews` | Lista todas las reseñas de un producto. | - |
| **POST** | `/{product_id}/reviews` | Envía una nueva reseña para un producto. | Body: `{rating, comentario, fotos[]}`, Requiere Login |

---

## 🛒 CAPA DE CARRITO
Base URL: `/api/v1/cart`

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Obtiene el carrito persistente del usuario. | Login Opcional |
| **POST** | `/add` | Añade un producto al carrito en la nube. | Body: `{productId, cantidad, personalizaciones}`, Requiere Login |
| **PATCH** | `/item/{id}` | Actualiza cantidad o personalizaciones de un item del carrito. | Body: `{cantidad?, personalizaciones?}`, Requiere Login |
| **DELETE** | `/item/{id}` | Elimina un item específico del carrito. | Requiere Login |
| **DELETE** | `/clear` | Vacía completamente el carrito. | Requiere Login |
| **POST** | `/apply-coupon` | Aplica un cupón de descuento al carrito actual. | Query: `?code=COFFEE10`, Requiere Login |

---

## 📦 CAPA DE PEDIDOS
Base URL: `/api/v1/orders`

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **POST** | `/checkout` | Finaliza la compra y crea el pedido. | Body: `{addressId, tipoPago, tipoPedido, notas?, propina?}`, Header: `X-Idempotency-Key`, Requiere Login |
| **GET** | `/` | Historial de pedidos del usuario. | Requiere Login |
| **GET** | `/active` | Lista pedidos en curso (pendientes, preparando, etc). | Requiere Login |
| **GET** | `/{id}` | Detalle de un pedido específico. | Requiere Login |
| **GET** | `/{id}/tracking` | Seguimiento en tiempo real (estados de preparación). | Requiere Login |
| **PATCH** | `/{id}/cancel` | Cancela un pedido (solo si está en estado 'pending'). | Requiere Login |

---

## 🤖 CAPA DE IA Y SOPORTE
Base URL: `/api/v1/chat` y rutas generales

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **POST** | `/chat/message` | Conversación por streaming con el Barista AI. | Body: `{message, conversationId?}`, Requiere Login |
| **GET** | `/chat/welcome` | Mensaje de bienvenida de IA con sugerencias. | - |
| **GET** | `/chat/history` | Historial de conversaciones de chat. | Requiere Login |
| **POST** | `/chat/recommendations` | Recomendaciones basadas en gustos/preferencias. | Body: `["string", ...]`, Requiere Login |
| **POST** | `/chat/recommendations/quiz` | Procesa un quiz para recomendar productos. | Body: `{answers}`, - |
| **GET** | `/promotions` | Lista promociones activas. | - |
| **POST** | `/coupons/validate` | Valida si un cupón es aplicable. | Query: `?code=XYZ` |
| **GET** | `/store/info` | Información de contacto y ubicación de la tienda. | - |
| **GET** | `/store/hours` | Horarios de apertura y estado actual. | - |
| **GET** | `/faq` | Preguntas frecuentes. | - |

---

## 👑 CAPA ADMINISTRATIVA (Dashboard)
Base URL: `/api/v1/admin`

| Método | Endpoint | Descripción | Requerimientos |
| :--- | :--- | :--- | :--- |
| **GET** | `/analytics` | **Optimizada.** Estadísticas, Deltas (crecimiento) y Desglose de ingresos reales. | Requiere Rol Admin |
| **GET** | `/orders` | Lista todos los pedidos del sistema con personalizaciones detalladas. | Requiere Rol Admin |
| **PATCH** | `/orders/{id}/status` | Actualiza el estado de preparación de un pedido. | Body: `{status}`, Requiere Rol Admin |
| **POST** | `/products` | Crea un nuevo producto en el catálogo. | Body: `{producto}`, Requiere Rol Admin |
| **PATCH** | `/products/{id}` | Actualiza parcialmente un producto existente. | Body: `{cambios}`, Requiere Rol Admin |
| **DELETE** | `/products/{id}` | Elimina o desactiva un producto. | Requiere Rol Admin |
| **GET** | `/notifications` | Lista notificaciones del sistema para el administrador. | Requiere Rol Admin |
| **PATCH** | `/notifications/{id}/read` | Marca notificación administrativa como leída. | Requiere Rol Admin |

---
*Documentación actualizada: mayo 2026*
