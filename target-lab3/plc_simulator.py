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
SUSTAIN_REQUIRED = 10
FLAG_PATH = "/flag/flag.txt"

INSTANCE_SEED = str(uuid.uuid4())
FLAG_HASH = hashlib.sha256(INSTANCE_SEED.encode()).hexdigest()[:16]
FLAG_TEXT = f"FLAG{{monitor_evasion_{FLAG_HASH}}}"

flag_written = False
streak = 0


def generate_flag():
    os.makedirs(os.path.dirname(FLAG_PATH), exist_ok=True)
    with open(FLAG_PATH, "w") as f:
        f.write(FLAG_TEXT + "\n")
    print(f"[MONITOR] Sustained anomaly detected. Flag written: {FLAG_TEXT}")


def monitor(context):
    global flag_written, streak
    while True:
        time.sleep(1)
        try:
            store = context[0]
            value = store.getValues(3, CRITICAL_REGISTER_ADDR, count=1)[0]

            if value >= ANOMALY_THRESHOLD:
                streak = min(streak + 1, SUSTAIN_REQUIRED)
                store.setValues(3, CRITICAL_REGISTER_ADDR, [INITIAL_VALUE])
                print(
                    f"[MONITOR] Anomalous value {value} detected and reset "
                    f"(streak {streak}/{SUSTAIN_REQUIRED})"
                )
                if streak >= SUSTAIN_REQUIRED and not flag_written:
                    generate_flag()
                    flag_written = True
            else:
                if flag_written:
                    print("[MONITOR] Condition normalized, flag state reset.")
                    flag_written = False
                streak = 0
        except Exception as e:
            print(f"[MONITOR] Error: {e}")


def build_identification():
    identity = ModbusDeviceIdentification()
    identity.VendorName = "Probatio Labs"
    identity.ProductCode = "PBL-SIM-03"
    identity.VendorUrl = "https://probatio-labs.local"
    identity.ProductName = "Simulated Boiler Controller"
    identity.ModelName = "PSB-2000"
    identity.MajorMinorRevision = "2.0.0"
    return identity


def clear_stale_flag():
    try:
        os.remove(FLAG_PATH)
        print(f"[TARGET] Removed stale flag from previous run: {FLAG_PATH}")
    except FileNotFoundError:
        pass


def main():
    clear_stale_flag()

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
    print(
        f"[MONITOR] Active: resets anomalies >= {ANOMALY_THRESHOLD} every 1s; "
        f"flag requires {SUSTAIN_REQUIRED} consecutive anomalies"
    )

    monitor_thread = threading.Thread(target=monitor, args=(context,), daemon=True)
    monitor_thread.start()

    StartTcpServer(context=context, identity=identity, address=("0.0.0.0", 502))


if __name__ == "__main__":
    main()
