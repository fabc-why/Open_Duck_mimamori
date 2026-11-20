"""COME_HERE intent definition."""

from kernel.understanding.models import IntentDefinition, SlotDefinition


COME_HERE = IntentDefinition(
    name="COME_HERE",
    description="話者がOpenDuckに、自分のところへ近づくよう依頼する",
    examples=(
        "こっち来て",
        "こっちに来て",
        "ここに来て",
        "近くまで来て",
        "ちょっと来て",
        "おいで",
        "おいでー"
    ),
    patterns=(
        r"^(?:ちょっと)?(?:こっち|こちら|ここ)(?:まで|に|へ)?来て(?:ください)?$",
        r"^(?:ちょっと)?近く(?:まで|に)?来て(?:ください)?$",
        r"^(?:ちょっと)?来て(?:ください)?$",
        r"^おいで$",
    ),
    priority=80,
    slots=(SlotDefinition(name="target", description="移動先", required=True),),
    slot_parser=lambda text: {"target": "speaker"},
)
