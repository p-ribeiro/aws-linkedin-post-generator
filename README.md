# AWS LinkedIn Post Generator

Gera carrosséis de LinkedIn a partir de capturas de tela de atividades AWS. Cada pasta de atividade vira um PDF com páginas no formato 3240×4050 px, prontas para publicação.

## Pré-requisitos

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

Instale as dependências:

```bash
uv sync
```

## Estrutura de pastas

```
screens/
├── Nome da Atividade 1/
│   ├── 1.1-descricao-da-tela.png
│   ├── 1.2-outra-tela.png
│   └── 2.1-terceira-tela.png
└── Nome da Atividade 2/
    └── 1.1-tela.png
out/          # PDFs e PNGs gerados aqui
logo.png      # Logo exibida no cabeçalho
```

### Convenção de nomes dos arquivos

Os arquivos de imagem devem seguir o padrão `GRUPO.ORDEM-descricao.png`:

- O **número antes do ponto** (`1`, `2`, `3`…) define o **grupo**. Imagens do mesmo grupo ficam na mesma página sempre que couberem.
- O **número após o ponto** define a **ordem** dentro do grupo.
- A **descrição** após o traço vira o título exibido acima da imagem (traços são substituídos por espaços).

Exemplos:
```
1.1-app-rodando.png      → grupo 1, ordem 1, título "app rodando"
1.2-logs-do-sistema.png  → grupo 1, ordem 2, título "logs do sistema"
2.1-pipeline.png         → grupo 2, ordem 1, nova página
```

## Uso

```bash
uv run make_post.py \
  --in_root screens \
  --out_dir out \
  --logo logo.png
```

Para cada subpasta em `--in_root`, o script gera:
- Um PNG por página (`NomeDaAtividade_p01.png`, `_p02.png`…)
- Um PDF único com todas as páginas (`NomeDaAtividade.pdf`)

### Opções avançadas

| Opção | Padrão | Descrição |
|---|---|---|
| `--width` | `3240` | Largura do canvas em pixels |
| `--height` | `4050` | Altura do canvas em pixels |
| `--margin` | `144` | Margem lateral em pixels |
| `--gap` | `72` | Espaço vertical entre frames |
| `--frame_pad` | `36` | Padding interno de cada frame |

## Como funciona

1. **Agrupamento** — imagens com o mesmo prefixo numérico ficam juntas na mesma página.
2. **Paginação** — se um grupo não cabe em uma página, o excedente vai para a próxima.
3. **Escala** — cada imagem é redimensionada para preencher a largura disponível. Se a altura resultante exceder o espaço da página, a escala é reduzida para caber, e o frame é centralizado horizontalmente.
4. **Renderização** — cada página recebe cabeçalho com logo e badge "Desafio AWS", título da atividade, e numeração quando há múltiplas páginas.
