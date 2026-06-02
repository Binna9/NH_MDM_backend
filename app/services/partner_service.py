from app.schemas.auth import LoginResponse, PartnerLoginRequest


MOCK_PARTNERS = {
    ("현웅빈", "000000", "1111111"): {
        "id": "1003",
        "name": "현웅빈",
    },
}


def authenticate_partner(payload: PartnerLoginRequest) -> LoginResponse | None:
    partner = MOCK_PARTNERS.get(
        (payload.name.strip(), payload.resident_front, payload.resident_back),
    )

    if partner is None:
        return None

    return LoginResponse(
        access_token=f"mock-partner-token-{partner['id']}",
        partner_id=partner["id"],
        partner_name=partner["name"],
    )
