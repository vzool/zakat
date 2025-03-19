from dataclasses import dataclass, field, fields
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

class Object:
    # Frozen implemention REF https://discuss.python.org/t/dataclasses-freezing-specific-fields-should-be-possible/59968/2
    def __post_init__(self):
        self.__set_fields_frozen(self)
    @classmethod
    def __set_fields_frozen(cls, self):
        flds = fields(cls)
        for fld in flds:
            if fld.metadata.get("frozen"):
                field_name = fld.name
                field_value = getattr(self, fld.name)
                setattr(self, f"_{fld.name}", field_value)

                def local_getter(self):
                    return getattr(self, f"_{field_name}")

                def frozen(name):
                    def local_setter(self, value):
                        raise RuntimeError(f"Field '{name}' is frozen!")
                    return local_setter

                setattr(cls, field_name, property(local_getter, frozen(field_name)))

@dataclass
class TransactionDetail(Object):
    capital: int #= field(metadata={"frozen": True})
    count: int
    last: int
    rest: int
    total: int

@dataclass
class TransactionLog:
    value: int
    desc: str
    ref: Optional[int]
    file: Dict[str, str] = field(default_factory=dict)

@dataclass
class AccountDetail:
    balance: int
    box: Dict[int, TransactionDetail] = field(default_factory=dict)
    count: int = field(default_factory=lambda x : 0)
    log: Dict[int, TransactionLog] = field(default_factory=dict)
    hide: bool = field(default_factory=lambda x : False)
    zakatable: bool = field(default_factory=lambda x : True)

@dataclass
class ExchangeRate:
    rate: float
    description: str

@dataclass
class HistoryAction:
    action: Action
    account: str
    ref: Optional[int]
    file: Optional[int]
    key: Optional[str]
    value: Optional[int]
    math: Optional[MathOperation]

@dataclass
class Vault:
    account: Dict[str, AccountDetail] = field(default_factory=dict)
    exchange: Dict[str, Dict[int, ExchangeRate]] = field(default_factory=dict)
    history: Dict[int, List[HistoryAction]] = field(default_factory=dict)
    lock: Optional[int] = None
    report: Dict[int, Tuple] = field(default_factory=dict)

# Example Usage
def create_dataclass_instance():
    y = Vault(
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
            "my_account" : {
                1234567890 : ExchangeRate(rate=1.0, description = "USD to local")
            }
        },
        history = {
            1678886400 : [HistoryAction(action = Action.CREATE, account = "my_account", ref =   None, file = None, key = None, value = None, math = None)]
        },
        lock=None,
        report={}
    )
    #print(id(y))
    return y

def access_dataclass_attribute(vault):
    return vault.account["my_account"].balance

if __name__ == "__main__":
    x = create_dataclass_instance()
    print(x)
