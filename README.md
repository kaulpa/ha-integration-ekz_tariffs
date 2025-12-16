# EKZ Energy Tariffs Integration for Home Assistant

A custom integration for Home Assistant that fetches energy tariff data from EKZ (Elektrizitätswerke des Kantons Zürich) API and provides detailed price information as sensors.

## Features

- Automatic daily updates of energy tariffs (configurable update time)
- Detailed price components:
  - Electricity prices (per kWh and base fee)
  - Grid prices (per kWh and base fee)
  - Regional fees (per kWh and base fee)
  - Integrated total prices
- 15-minute interval price data
- Lowest price period detection
- Manual refresh capability via service call
- Visualization support

## Installation

### Option 1: Installation via HACS (Recommended)

1. Install [HACS](https://hacs.xyz) in your Home Assistant instance if not already installed
2. Open HACS in Home Assistant
3. Click on "Integrations"
4. Click the "+" button in the bottom right corner
5. Search for "EKZ Energy Tariffs"
6. Click on the result and select "Install"
7. Restart Home Assistant
8. Go to Settings > Devices & Services > Integrations
9. Click the "+" button to add a new integration
10. Search for "EKZ Energy Tariffs" and follow the configuration steps

### Option 2: Manual Installation

1. Download the latest release from [GitHub](https://github.com/kaulpa/ha-integration-ekz_tariffs/releases)
2. Copy the `ekz_tariffs` folder from `custom_components` to your Home Assistant's `custom_components` directory
3. Restart Home Assistant
4. Go to Settings > Devices & Services > Integrations
5. Click the "+" button to add a new integration
6. Search for "EKZ Energy Tariffs" and follow the configuration steps

### Configuration

After installation:
1. Set the update time (when to fetch new data each day, default is 18:00)
2. Optionally provide your customer number (if required for your tariff data)

## Available Entities

The integration creates a sensor with the following information:

### Main Sensor: `sensor.ekz_energy_tariff`
- **State**: Current integrated price (CHF/kWh)
- **Attributes**:
  - `electricity_CHF_per_kWh`: Current electricity price per kWh
  - `electricity_CHF_per_M`: Current electricity base fee
  - `grid_CHF_per_kWh`: Current grid price per kWh
  - `grid_CHF_per_M`: Current grid base fee
  - `integrated_CHF_per_kWh`: Current total price per kWh
  - `integrated_CHF_per_M`: Current total base fee
  - `regional_fees_CHF_per_kWh`: Current regional fees per kWh
  - `regional_fees_CHF_per_M`: Current regional fees base amount
  - `current_period_start`: Start time of current period
  - `current_period_end`: End time of current period
  - `lowest_price`: Lowest upcoming price
  - `lowest_price_time`: When the lowest price period starts
  - `lowest_price_duration`: Duration of lowest price period in minutes
  - `next_update`: When the next data update will occur

## Services

### Service: `ekz_tariffs.refresh_data`
Manually refresh the tariff data from the EKZ API.

You can call this service from:
- Developer Tools > Actions
- Automations/Scripts using: `service: ekz_tariffs.refresh_data`
- REST API: `/api/services/ekz_tariffs/refresh_data`

## Visualization Examples

### Basic Price Card
```yaml
type: sensor
entity: sensor.ekz_energy_tariff
name: Current Energy Price
```

### Detailed Price Card
```yaml
type: entities
entities:
  - entity: sensor.ekz_energy_tariff
    name: Total Price
    secondary_info: last-updated
  - attribute: electricity_CHF_per_kWh
    entity: sensor.ekz_energy_tariff
    name: Electricity Price
  - attribute: grid_CHF_per_kWh
    entity: sensor.ekz_energy_tariff
    name: Grid Price
  - attribute: regional_fees_CHF_per_kWh
    entity: sensor.ekz_energy_tariff
    name: Regional Fees
```

### Price Graph (using ApexCharts Card)
```yaml
type: custom:apexcharts-card
header:
  title: Energy Prices
  show: true
graph_span: 24h
span:
  start: day
  offset: +24h
series:
  - entity: sensor.ekz_energy_tariff
    type: column
    float_precision: 2
    name: Energy Price
    unit: CHF/kWh
```

## API Information

The integration uses the EKZ Tariffs API:
- Endpoint: https://api.tariffs.ekz.ch/v1/tariffs
- Update frequency: Daily until 18:00 CET (configurable)
- Data provided: Next day's energy prices in 15-minute intervals

## Configuration

The integration can be configured through the UI. Available options:
- **Update Time**: When to fetch new data each day (default: 18:00)

## Troubleshooting

If you encounter issues:

1. Check that the EKZ API is accessible from your Home Assistant instance
2. Verify your update time is set correctly (after EKZ publishes their data)
3. Check Home Assistant logs for any error messages
4. Use the manual refresh service to force a data update
5. Ensure your Home Assistant's time zone is correctly set

## Contributing

Feel free to submit issues and pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
