import attrs
from typing import Dict, Optional, List, Tuple
from enum import Enum

class Action(Enum):
    CREATE = "CREATE"
    TRACK = "TRACK"
    LOG = "LOG"
    SUB = "SUB"
    ADD_FILE = "ADD_FILE"
    REMOVE_FILE = "REMOVE_FILE"
    BOX_TRANSFER = "BOX_TRANSFER"
    EXCHANGE = "EXCHANGE"
    REPORT = "REPORT"
    ZAKAT = "ZAKAT"

class MathOperation(Enum):
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"

@attrs.define
class TransactionDetail:
    capital: int
    count: int
    last: int
    rest: int
    total: int

@attrs.define
class TransactionLog:
    value: int
    desc: str
    ref: Optional[int]
    file: Dict[str, str] = attrs.field(factory=dict)

@attrs.define
class AccountDetail:
    balance: int
    count: int
    hide: bool
    zakatable: bool
    box: Dict[int, TransactionDetail] = attrs.field(factory=dict)
    log: Dict[int, TransactionLog] = attrs.field(factory=dict)

@attrs.define
class ExchangeRate:
    rate: float
    description: str

@attrs.define
class HistoryAction:
    action: Action
    account: str
    ref: Optional[int]
    file: Optional[int]
    key: Optional[str]
    value: Optional[int]
    math: Optional[MathOperation]

@attrs.define
class Vault:
    account: Dict[str, AccountDetail] = attrs.field(factory=dict)
    exchange: Dict[str, Dict[int, ExchangeRate]] = attrs.field(factory=dict)
    history: Dict[int, List[HistoryAction]] = attrs.field(factory=dict)
    lock: Optional[int] = None
    report: Dict[int, Tuple] = attrs.field(factory=dict)

# Example Usage
def create_attrs_instance():
    vault = Vault(
        account={
            "my_account": AccountDetail(
                balance=500,
                box={
                    1678886400: TransactionDetail(capital=500, count=0, last=0, rest=500, total=0)
                },
                count=1,
                log={
                    1678886400: TransactionLog(value=500, desc="Deposit", ref=1678886400, file={})
                },
                hide=False,
                zakatable=True,
            )
        },
        exchange = {
            "my_account{" : {
                1234567890 : ExchangeRate(rate=1.0, description = "USD to local")
            }
        },
        history = {
            1678886400 : [HistoryAction(action = Action.CREATE, account = "my_account", ref =   None, file = None, key = None, value = None, math = None)]
        },
        lock=None,
        report={}
    )
    return vault

def access_attrs_attribute(vault):
    return vault.account["my_account"].balance

if __name__ == "__main__":
    vault = create_attrs_instance()
    print(vault)