from homeassistant.const import UnitOfTemperature


def correct_temperature_value(
    temperature_unit: UnitOfTemperature, temperature: float
) -> float:
    if temperature and temperature_unit == UnitOfTemperature.FAHRENHEIT:
        temperature = (round(temperature * 9 / 5 + 32 + 0.01) - 32) / 9 * 5

    return temperature
