import hashlib
import os
import time
import threading
import uuid

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartTcpServer

CRITICAL_REGISTER_ADDR = 0
NUM_HOLDING_REGISTERS = 100
INITIAL_VALUE = 50
ANOMALY_THRESHOLD = 150
FLAG_PATH = "/flag/flag.txt"

INSTANCE_SEED = str(uuid.uuid4())
FLAG_HASH = hashlib.sha256(INSTANCE_SEED.encode()).hexdigest()[:16]
FLAG_TEXT = f"FLAG{{modbus_no_auth_{FLAG_HASH}}}"

flag_written = False


def generate_flag():
    os.makedirs(os.path.dirname(FLAG_PATH), exist_ok=True)
    with open(FLAG_PATH, "w") as f:
        f.write(FLAG_TEXT + "\n")
    print(f"[WATCHER] Flag written to {FLAG_PATH}: {FLAG_TEXT}")


def watcher(store):
    global flag_written
    while True:
        time.sleep(1)
        try:
            context = store[0]
            value = context.getValues(3, CRITICAL_REGISTER_ADDR, count=1)[0]
            print(f"[WATCHER] CRITICAL_REGISTER={value}")

            if value >= ANOMALY_THRESHOLD and not flag_written:
                generate_flag()
                flag_written = True

            if flag_written and 20 <= value <= 80:
                print("[WATCHER] Value returned to normal range, resetting flag state.")
                flag_written = False
        except Exception as e:
            print(f"[WATCHER] Error: {e}")


def build_identification():
    identity = ModbusDeviceIdentification()
    identity.VendorName = "Probatio Labs"
    identity.ProductCode = "PBL-SIM-01"
    identity.VendorUrl = "https://probatio-labs.local"
    identity.ProductName = "Simulated Boiler Controller"
    identity.ModelName = "PSB-2000"
    identity.MajorMinorRevision = "1.0.0"
    return identity


def main():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * NUM_HOLDING_REGISTERS),
        co=ModbusSequentialDataBlock(0, [0] * NUM_HOLDING_REGISTERS),
        hr=ModbusSequentialDataBlock(0, [INITIAL_VALUE] + [0] * (NUM_HOLDING_REGISTERS - 1)),
        ir=ModbusSequentialDataBlock(0, [0] * NUM_HOLDING_REGISTERS),
        zero_mode=True,
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = build_identification()

    print("[TARGET] Starting Modbus/TCP server on 0.0.0.0:502")
    print(f"[TARGET] Instance seed: {INSTANCE_SEED}")
    print(f"[TARGET] Holding register 0 initialized to {INITIAL_VALUE}")

    watcher_thread = threading.Thread(target=watcher, args=(context,), daemon=True)
    watcher_thread.start()

    StartTcpServer(context=context, identity=identity, address=("0.0.0.0", 502))


if __name__ == "__main__":
    main()
