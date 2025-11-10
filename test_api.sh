#!/usr/bin/env bash
set -euo pipefail

API_URL="http://localhost:8000"
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImpvYW8uc2lsdmEiLCJ0aXBvX3VzdWFyaW8iOiJnZXJlbnRlIiwiZXhwIjoxNzYyODEwNDg1LCJpYXQiOjE3NjI4MDk1ODUsInR5cGUiOiJhY2Nlc3MifQ.-ytDGqnGnxHE5cTmp-AsF6YzR0YtiIQP-kvAaagteYU"
AUTH_HEADER="Authorization: Bearer ${ACCESS_TOKEN}"
PRODUCT_ID=4
CHECKOUT_CPF="49209207840"
PAYMENT_METHOD="Credito"
DISCOUNT=0.0

echo "== Ver perfil (/auth/me) =="
curl -sS -X GET "${API_URL}/auth/me" -H "${AUTH_HEADER}" -H "Accept: application/json" | jq || true
echo; echo

echo "== Adicionar item ao carrinho (POST /sales/cart/items) =="
curl -sS -X POST "${API_URL}/sales/cart/items" \
  -H "${AUTH_HEADER}" -H "Content-Type: application/json" \
  -d "{\"produto_id\": ${PRODUCT_ID}, \"quantidade\": 2}" | jq || true
echo; echo

echo "== Ver carrinho (GET /sales/cart) =="
curl -sS -X GET "${API_URL}/sales/cart" -H "${AUTH_HEADER}" | jq || true
echo; echo

echo "== Alterar quantidade (PATCH /sales/cart/items/{id}) =="
curl -sS -X PATCH "${API_URL}/sales/cart/items/${PRODUCT_ID}" \
  -H "${AUTH_HEADER}" -H "Content-Type: application/json" \
  -d "{\"nova_quantidade\": 3}" | jq || true
echo; echo

echo "== Remover item (DELETE /sales/cart/items/{id}) =="
curl -sS -X DELETE "${API_URL}/sales/cart/items/${PRODUCT_ID}" -H "${AUTH_HEADER}" | jq || true
echo; echo

echo "== Adicionar item novamente para checkout =="
curl -sS -X POST "${API_URL}/sales/cart/items" \
  -H "${AUTH_HEADER}" -H "Content-Type: application/json" \
  -d "{\"produto_id\": ${PRODUCT_ID}, \"quantidade\": 1}" | jq || true
echo; echo

echo "== Finalizar venda (POST /sales/checkout) =="
curl -sS -X POST "${API_URL}/sales/checkout" \
  -H "${AUTH_HEADER}" -H "Content-Type: application/json" \
  -d "{\"cpf_cliente\": \"${CHECKOUT_CPF}\", \"forma_pagamento\": \"${PAYMENT_METHOD}\", \"percentual_desconto\": ${DISCOUNT}}" | jq || true
echo; echo

echo "== Buscar produto (GET /products/search?nome=Notebook) =="
curl -sS -G "${API_URL}/products/search" -H "${AUTH_HEADER}" --data-urlencode "nome=Notebook" | jq || true
echo; echo

echo "== Limpar carrinho (DELETE /sales/cart) =="
curl -sS -X DELETE "${API_URL}/sales/cart" -H "${AUTH_HEADER}" | jq || true
echo; echo

echo "== Fim =="