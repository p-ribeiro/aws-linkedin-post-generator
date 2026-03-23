# linkedin-aws-post-generator

Gera carrosséis de LinkedIn a partir de capturas de tela de atividades AWS. Cada pasta de atividade vira um PDF com páginas no formato 3240×4050 px, prontas para publicação.

## Instalação

Você precisa ter Python 3.10 ou superior instalado.

```bash
pip install git+https://github.com/YOUR_USERNAME/create-post-linkedin.git
```

Isso instala o comando `linkedin-aws-post-generator` diretamente no seu terminal.

## Estrutura de pastas

Organize suas capturas de tela assim antes de rodar:

```
pages/
├── Nome da Atividade 1/
│   ├── 0.txt              ← (opcional) capa do PDF
│   ├── 1.txt              ← (opcional) título do grupo 1
│   ├── 1.1-descricao-da-tela.png
│   ├── 1.2-outra-tela.png
│   ├── 2.txt              ← (opcional) título do grupo 2
│   └── 2.1-terceira-tela.png
└── Nome da Atividade 2/
    ├── 1.txt
    └── 1.1-tela.png
result/       # PDFs e PNGs gerados aqui (criado automaticamente)
logo.png      # Logo exibida no cabeçalho
```

### Página de capa

Se existir um arquivo `0.txt` na pasta da atividade, ele é usado como **capa do PDF** — a primeira página do carrossel. O texto vira o título centralizado da capa.

A capa usa a mesma paleta de cores das demais páginas, mas com um layout diferente: logo centralizada no topo, linha divisória laranja, título em destaque no centro e cubos isométricos nos quatro cantos.

Exemplo de `0.txt`:
```
Implantando uma Aplicação Containerizada na AWS com ECS e Fargate
```

### Página de título por grupo

Cada grupo de imagens (`1.x`, `2.x`, `3.x`…) pode ter sua própria página de título. Basta criar um arquivo de texto com o número do grupo na pasta da atividade:

| Arquivo | Aparece antes de |
|---|---|
| `1.txt` | todas as imagens `1.x` |
| `2.txt` | todas as imagens `2.x` |
| `3.txt` | todas as imagens `3.x` |

O texto é centralizado na página e quebrado automaticamente para caber na largura. O arquivo é opcional — grupos sem `.txt` não geram página de título.

Exemplo de `1.txt`:
```
Neste laboratório configuramos um bucket S3 com versionamento habilitado e testamos o ciclo de vida dos objetos.
```

### Convenção de nomes dos arquivos

Os arquivos devem seguir o padrão `GRUPO.ORDEM-descricao.png`:

- O **número antes do ponto** (`1`, `2`, `3`…) define o **grupo**. Imagens do mesmo grupo ficam na mesma página.
- O **número após o ponto** define a **ordem** dentro do grupo.
- A **descrição** após o traço vira o rótulo exibido acima da imagem (traços viram espaços).

```
1.1-app-rodando.png      → grupo 1, ordem 1, rótulo "app rodando"
1.2-logs-do-sistema.png  → grupo 1, ordem 2, rótulo "logs do sistema"
2.1-pipeline.png         → grupo 2, ordem 1, nova página
```

## Uso

```bash
linkedin-aws-post-generator
```

As pastas `pages/` e `result/` e o arquivo `logo.png` são usados por padrão. Use os argumentos abaixo para caminhos diferentes:

```bash
linkedin-aws-post-generator --input screenshots --output out --logo minha-logo.png
```

Use `--activity` para processar apenas uma atividade específica:

```bash
linkedin-aws-post-generator --activity "Nome da Atividade 1"
```

Para cada subpasta em `--input`, o comando gera:
- Um PNG por página (`NomeDaAtividade_p00.png` para a capa, `_p01.png`, `_p02.png`… para as demais)
- Um PDF único com todas as páginas (`NomeDaAtividade.pdf`)

### Opções avançadas

| Opção | Padrão | Descrição |
|---|---|---|
| `--input` | `pages` | Pasta com as subpastas de atividades |
| `--output` | `result` | Pasta onde os arquivos gerados são salvos |
| `--logo` | `logo.png` | Caminho para o arquivo de logo |
| `--activity` | *(todas)* | Processa apenas esta pasta de atividade (pode ser repetido) |
| `--width` | `3240` | Largura do canvas em pixels |
| `--height` | `4050` | Altura do canvas em pixels |
| `--margin` | `144` | Margem lateral em pixels |
| `--gap` | `72` | Espaço vertical entre frames |
| `--frame_pad` | `36` | Padding interno de cada frame |

## Como funciona

1. **Capa** — se `0.txt` existir, a primeira página do PDF é uma capa com logo centralizada, linha laranja e título em destaque.
2. **Agrupamento** — imagens com o mesmo prefixo numérico ficam juntas na mesma página.
3. **Paginação** — se um grupo não cabe em uma página, o excedente vai para a próxima.
4. **Escala** — cada imagem é redimensionada para preencher a largura disponível sem ultrapassar a altura da página.
5. **Renderização** — cada página recebe cabeçalho com logo e badge, título da atividade e numeração quando há múltiplas páginas.
