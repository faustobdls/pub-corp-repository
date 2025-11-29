# Pub Corp Repository - Guia de Uso

Este guia explica como configurar o servidor, preparar o ambiente de desenvolvimento e utilizar o repositório privado.

## 🚀 Configuração do Servidor

### 1. Pré-requisitos
- Python 3.11+
- Pip
- Virtualenv (recomendado)

### 2. Instalação

1. Clone o repositório e entre na pasta:
   ```bash
   git clone <url-do-repo>
   cd pub-corp-repository
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuração (.env)

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Configuração do Servidor
HOST=0.0.0.0
PORT=5002
DEBUG=True

# Autenticação (Token para publicar e baixar pacotes privados)
AUTH_TOKEN=seu-token-secreto-aqui

# Armazenamento (local ou gcp)
STORAGE_TYPE=local
LOCAL_STORAGE_DIR=./storage

# Configuração GCP (apenas se STORAGE_TYPE=gcp)
# GCP_PROJECT_ID=seu-projeto-id
# GCP_BUCKET_NAME=seu-bucket-nome
```

### 4. Executando o Servidor

```bash
python run.py
```
O servidor iniciará em `http://localhost:5002` (ou na porta configurada).

---

## 💻 Configuração da Máquina do Desenvolvedor

Para que o `dart` ou `flutter` utilizem este repositório privado, siga os passos abaixo.

### 1. Configurar a URL do Repositório

Defina a variável de ambiente `PUB_HOSTED_URL` para apontar para o seu servidor.

**Temporário (apenas para o terminal atual):**
```bash
export PUB_HOSTED_URL=http://localhost:5002
```

**Permanente (Linux/Mac - Bash/Zsh):**
Adicione ao seu `~/.bashrc` ou `~/.zshrc`:
```bash
export PUB_HOSTED_URL=http://localhost:5002
```

### 2. Configurar Autenticação

Para baixar ou publicar pacotes privados, você precisa autenticar o cliente Dart com o servidor.

Execute o comando abaixo, substituindo `seu-token-secreto-aqui` pelo valor definido no `.env` do servidor:

```bash
dart pub token add http://localhost:5002 --env-var PUB_HOSTED_URL
```
*Nota: O comando acima pode pedir para você colar o token manualmente.*

Alternativamente, você pode configurar manualmente editando o arquivo de tokens do pub (geralmente em `~/.pub-cache/credentials.json` ou similar, mas o comando `token add` é o método recomendado).

---

## 📦 Publicando Pacotes

### Método Padrão (Dart Pub Publish)

1. No `pubspec.yaml` do seu pacote, adicione a configuração de publicação (opcional se `PUB_HOSTED_URL` estiver setado, mas recomendado para clareza):
   ```yaml
   publish_to: 'http://localhost:5002'
   ```

2. Publique o pacote:
   ```bash
   dart pub publish
   ```

### Método Manual (cURL)

Você também pode fazer upload manual de um arquivo `.tar.gz`:

```bash
curl -X POST \
  -H "Authorization: Bearer seu-token-secreto-aqui" \
  -F "file=@pacote-1.0.0.tar.gz" \
  http://localhost:5002/api/packages
```

---

## 📥 Baixando Pacotes

Basta adicionar o pacote ao seu `pubspec.yaml`. Se o pacote existir no repositório privado, ele será baixado de lá. Caso contrário, o servidor fará proxy para o `pub.dev`.

```yaml
dependencies:
  meu_pacote_privado: ^1.0.0
  http: ^1.0.0  # Será buscado no pub.dev via proxy
```

Execute:
```bash
flutter pub get
```

---

## 🛠 Solução de Problemas

**Erro: `Invalid token`**
- Verifique se o token configurado na máquina do desenvolvedor coincide com o `AUTH_TOKEN` no `.env` do servidor.
- Tente remover e adicionar o token novamente: `dart pub token remove http://localhost:5002` e depois `add`.

**Erro: `Injecting Any is not supported`**
- Certifique-se de que está rodando a versão mais recente do código do servidor, onde as injeções de dependência foram corrigidas.

**Erro: `Connection refused`**
- Verifique se o servidor está rodando (`python run.py`).
- Verifique se a porta no `PUB_HOSTED_URL` está correta.