from services.seguranca import confere_senha, gerar_hash


def test_hash_nao_contem_a_senha_e_confere():
    guardado = gerar_hash("segredo1")
    assert "segredo1" not in guardado
    assert confere_senha("segredo1", guardado)
    assert not confere_senha("outra", guardado)


def test_mesma_senha_gera_hashes_diferentes():
    assert gerar_hash("x12345") != gerar_hash("x12345")


def test_valor_guardado_corrompido_nao_confere():
    assert not confere_senha("x", "lixo")
    assert not confere_senha("x", "zz$zz")
