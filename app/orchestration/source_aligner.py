import re

from app.schemas.evidence import EvidenceRef


def _tokens(text: str) -> set[str]:
    """Tách từ tiếng Việt / tiếng Anh thành tập hợp các token."""
    return set(re.findall(r"[\wÀ-ỹ]+", text.lower()))


def align_sources(
    evidence: list[EvidenceRef],
    threshold: float = 0.25,
) -> list[dict]:
    """Gom nhóm các bằng chứng (evidence) tương đồng dựa trên Jaccard Similarity.

    Args:
        evidence: Danh sách các đối tượng EvidenceRef.
        threshold: Ngưỡng độ tương đồng Jaccard tối thiểu để gom nhóm (default: 0.25).

    Returns:
        Danh sách các dictionary nhóm bằng chứng.
    """
    groups: list[dict] = []

    for item in evidence:
        item_tokens = _tokens(item.content)
        best_group = None
        best_score = 0.0

        for group in groups:
            group_tokens = _tokens(group["representative_text"])
            
            # Score = Giao / Hợp
            score = len(item_tokens & group_tokens) / len(item_tokens | group_tokens) if union else 0.0

            if score > best_score:
                best_group = group
                best_score = score

        if best_group and best_score >= threshold:
            best_group["evidence_ids"].append(item.evidence_id)
        else:
            groups.append(
                {
                    "group_id": f"GROUP_{len(groups) + 1:03d}",
                    "representative_text": item.content,
                    "evidence_ids": [item.evidence_id],
                }
            )

    return groups


if __name__ == "__main__":
    print(align_sources([]))
