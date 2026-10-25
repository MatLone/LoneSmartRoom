"""Declared slots, NOT detected hardware. No I/O is performed here."""
from .contracts import Cadence as C, MetricSpec as M, Unit as U

DEFAULT_METRICS = (
    M('cpu.utilization', 'cpu', 'Intel Core i5-12400 · utilização', U.PERCENT, C.FAST),
    M('cpu.package_temperature', 'cpu', 'Intel Core i5-12400 · CPU Package', U.CELSIUS, C.THERMAL),
    M('gpu.utilization', 'gpu.amd', 'Radeon RX 6750 XT · utilização', U.PERCENT, C.FAST),
    M('gpu.temperature', 'gpu.amd', 'Radeon RX 6750 XT · temperatura', U.CELSIUS, C.THERMAL),
    M('gpu.hotspot_temperature', 'gpu.amd', 'Radeon RX 6750 XT · hotspot', U.CELSIUS, C.THERMAL),
    M('gpu.vram_total', 'gpu.amd', 'VRAM · total', U.BYTES, C.CAPACITY),
    M('gpu.vram_used', 'gpu.amd', 'VRAM · utilizada', U.BYTES, C.FAST),
    M('gpu.vram_available', 'gpu.amd', 'VRAM · disponível', U.BYTES, C.FAST),
    M('gpu.fan_rpm', 'gpu.amd', 'Ventoinha GPU · RPM, se suportado', U.RPM, C.THERMAL),
    M('ram.total', 'ram', 'RAM DDR4 · total utilizável', U.BYTES, C.FAST),
    M('ram.used', 'ram', 'RAM · utilizada', U.BYTES, C.FAST),
    M('ram.available', 'ram', 'RAM · disponível', U.BYTES, C.FAST),
    M('ram.utilization', 'ram', 'RAM · utilização', U.PERCENT, C.FAST),
    M('storage.system.total', 'storage.system', 'Volume do sistema · capacidade', U.BYTES, C.CAPACITY),
    M('storage.system.used', 'storage.system', 'Volume do sistema · utilizado', U.BYTES, C.CAPACITY),
    M('storage.system.available', 'storage.system', 'Volume do sistema · disponível à conta', U.BYTES, C.CAPACITY),
    M('storage.system.free', 'storage.system', 'Volume do sistema · livre', U.BYTES, C.CAPACITY),
    M('storage.system.activity', 'storage.system', 'Disco do sistema · tempo ativo', U.PERCENT, C.FAST),
    M('storage.system.read_rate', 'storage.system', 'Disco do sistema · leitura', U.BYTES_PER_SECOND, C.FAST),
    M('storage.system.write_rate', 'storage.system', 'Disco do sistema · escrita', U.BYTES_PER_SECOND, C.FAST),
    M('fan.cpu.rpm', 'fan.cpu', 'Ventoinha CPU · slot não detectado', U.RPM, C.THERMAL),
    M('fan.chassis.rpm', 'fan.chassis', 'Ventoinha gabinete · slot não detectado', U.RPM, C.THERMAL),
)
