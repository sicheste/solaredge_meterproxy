# solaredge_meterproxy

solaredge_meterproxy is a python tool that proxies Modbus requests from SolarEdge power inverters to unsupported kWh meters. While SolarEdge only supports a [limited number](https://www.solaredge.com/se-supported-devices) of revenue meters, by masquerading as a supported meter it is possible to supply your own meter values to the SolarEdge inverter for production, consumption, import/export monitoring, and export limitation.