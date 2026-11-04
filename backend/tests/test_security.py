from app.security import hash_password, verify_password


def test_hash_and_verify():
    password = "uma-senha-de-teste-muito-forte"
    hashed = hash_password(password)
    assert password not in hashed
    assert verify_password(password, hashed)
    assert not verify_password("senha-errada", hashed)
