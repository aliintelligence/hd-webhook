# Home Depot Zapier Webhook

Webhook server that creates leads in Home Depot Service Center and returns the Service Center ID (F-number) for contract population.

## Features

- ✅ Creates leads in Home Depot HDSC
- ✅ Returns Service Center ID (F-number) for contracts
- ✅ Includes appointment scheduling
- ✅ No external dependencies (uses Python stdlib)
- ✅ Auto-retries for Service Center ID lookup

## Deployment

This webhook is deployed on Railway.app

## API Endpoint

**POST /create-lead**

Creates a lead and returns the Service Center ID.

### Request Body

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "3051234567",
  "email": "john@example.com",
  "address": "123 Main St",
  "city": "Miami",
  "state": "FL",
  "zip_code": "33186",
  "store_id": "0207",
  "appointment_date": "12/01/2025",
  "appointment_time": "10:00"
}
```

**Required Fields**: `first_name`, `last_name`, `phone`, `address`, `city`, `state`, `zip_code`, `store_id`

### Response

```json
{
  "success": true,
  "service_center_id": "F54933529",
  "customer_name": "John Doe",
  "appointment_date": "12/01/2025 10:00:00"
}
```

## Use in Zapier

In your PDF Filler step, map:
- **Service Center ID field**: `{{Webhooks by Zapier: Service Center ID}}`

## Health Check

**GET /health**

Returns server status.
