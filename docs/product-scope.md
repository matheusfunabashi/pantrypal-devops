# PantryPal — Product Scope

## 1. Product Overview

PantryPal is a web application that helps people keep track of food products they have at home and check product information before purchasing groceries.

Users can search for products using barcodes, add products to their pantry, manage quantities, and view nutritional information obtained from Open Food Facts.

## 2. Problem

People sometimes forget which products they already have at home, resulting in duplicate purchases and poor pantry organization.

Additionally, checking a product's nutritional classification while shopping is not always convenient.

## 3. Target Users

People who want a simple way to manage their household food inventory, especially students and people living in shared apartments.

## 4. MVP Features

### Product Lookup
- Users can manually enter a product barcode.
- The application retrieves product information from Open Food Facts.
- Product details include name, brand, image, and Nutri-Score when available.
- Retrieved information is cached in the Catalog database.
- Unknown products and missing information are handled gracefully.

### Pantry Management
- Users can add a product to their pantry with a quantity.
- Users can view their saved pantry items.
- Users can change the quantity of an existing item.
- Users can delete items.
- Data persists in the Pantry database.

### Check Before You Buy
- Users can look up a product without adding it to their pantry.
- The product's Nutri-Score is displayed when available.

## 5. Product Rules

- Barcodes are stored as strings to preserve leading zeros.
- Quantities are positive whole numbers.
- Each barcode appears at most once in the demo pantry.
- Adding an existing barcode increases its quantity.
- Setting quantity to zero is not allowed; users delete an item instead.
- Products not found on Open Food Facts cannot be added in the initial MVP.
- Missing Nutri-Score values are displayed as "Not available".
- No real user authentication is required.

## 6. Architecture

The application consists of exactly two backend services and one static frontend.

**Pantry Service:** Manages inventory records and quantities using its own SQL database.

**Catalog Service:** Retrieves product information from Open Food Facts and caches results in a separate SQL database.

The Pantry Service communicates with the Catalog Service over HTTP when it needs product information.

The static frontend communicates with both services.

## 7. Technology Stack

- Backend: Python and FastAPI
- Frontend: HTML, CSS, and JavaScript
- Local databases: SQL Server
- Production databases: Azure SQL Database
- Containers: Docker
- CI/CD: GitHub Actions and GHCR
- Hosting: Azure Container Apps and Azure Static Web Apps

## 8. Out of Scope

The initial MVP will not implement:
- Real user accounts or authentication.
- Multiple household accounts.
- Payments.
- AI recommendations.
- Notifications.

## 9. Optional Enhancements

Only if all mandatory requirements are completed:
- Camera-based barcode scanning.
- Expiry-date tracking.
- Running-low inventory view.

## 10. Sprint-Level Product Goals

**Sprint 0:** Define the product, establish the development workflow, and create a local application skeleton.

**Sprint 1:** Deploy the application through CI/CD and implement barcode lookup, caching, and pantry CRUD.

**Sprint 2:** Complete the check-before-buy experience, improve reliability, implement monitoring, and finalize documentation.
