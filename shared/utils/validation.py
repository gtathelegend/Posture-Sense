from typing import Any, Dict
from shared.contracts.base import BaseContract
from shared.constants.errors import ErrorCodes


class ContractValidator:
    """Validates contract structures before events enter the EventBus."""

    REQUIRED_METADATA_FIELDS = {"id", "timestamp", "schema_version", "source"}

    @classmethod
    def validate_contract(cls, contract: Any) -> bool:
        if isinstance(contract, BaseContract):
            data = contract.to_dict()
        elif isinstance(contract, dict):
            data = contract
        else:
            raise ValueError(f"[{ErrorCodes.INVALID_CONTRACT}] Contract must be BaseContract instance or dict.")

        missing = cls.REQUIRED_METADATA_FIELDS - set(data.keys())
        if missing:
            raise ValueError(
                f"[{ErrorCodes.SCHEMA_VALIDATION_FAILED}] Contract missing required metadata fields: {missing}"
            )

        return True
