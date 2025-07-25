# Verificador IPTV Otimizado

Versão simplificada e otimizada do verificador de credenciais IPTV com suporte a arquivos locais e GitHub Gist.

## Características

- ✅ **Simples e rápido**: Foco em um servidor por vez
- 📁 **Suporte a arquivos locais**: Carrega combos da pasta `./combo`
- 🌐 **Suporte a GitHub Gist**: Baixa combos diretamente de gists
- 🎯 **Auto-criação de pastas**: Cria automaticamente as pastas `combo` e `hits`
- 📊 **Progresso em tempo real**: Mostra progresso e hits encontrados
- 💾 **Salvamento organizado**: Hits salvos por servidor na pasta `hits`

## Instalação

```bash
pip install aiohttp aiofiles
```

## Uso

### Modo Interativo (Recomendado)

```bash
python iptv_checker_optimized.py
```

O modo interativo guia você através das opções:

1. **Escolha do combo**:
   - Arquivo local (pasta `./combo`)
   - GitHub Gist (usuário/gist)

2. **Configuração do servidor**: Um servidor por verificação

3. **Configurações opcionais**: Requisições simultâneas e timeout

### Modo Linha de Comando

```bash
# Arquivo local
python iptv_checker_optimized.py --combo ./combo/meucombo.txt --server http://exemplo.com

# URL do combo
python iptv_checker_optimized.py --combo-url https://raw.githubusercontent.com/user/gist/file.txt --server http://exemplo.com

# Com configurações personalizadas
python iptv_checker_optimized.py --combo ./combo/teste.txt --server http://exemplo.com --concurrent 50 --timeout 10
```

## Estrutura de Pastas

```
./
├── iptv_checker_optimized.py
├── combo/                    # Coloque seus arquivos .txt aqui
│   ├── combo1.txt
│   └── combo2.txt
└── hits/                     # Hits salvos automaticamente
    ├── exemplo_com.txt
    └── servidor2_com.txt
```

## Formato do Combo

Os arquivos de combo devem ter o formato:
```
usuario1:senha1
usuario2:senha2
usuario3:senha3
```

## Parâmetros

- `--combo`: Caminho para arquivo local de credenciais
- `--combo-url`: URL do combo online
- `--server`: Servidor IPTV para testar (obrigatório)
- `--concurrent`: Número de requisições simultâneas (padrão: 30)
- `--timeout`: Timeout em segundos (padrão: 8)
- `--interactive`: Força modo interativo

## Melhorias da Versão Otimizada

### Performance
- Reduzido requisições simultâneas padrão para 30 (mais estável)
- Timeout reduzido para 8 segundos (mais rápido)
- Processamento em lotes de 100 credenciais
- Menos overhead de threads

### Simplicidade
- Foco em um servidor por vez (mais eficiente)
- Interface mais limpa e direta
- Menos opções confusas
- Criação automática de pastas

### Confiabilidade
- Melhor tratamento de erros
- Validação de entrada mais robusta
- Menos dependências
- Código mais limpo e manutenível

## Exemplo de Uso Completo

1. **Preparar combo**:
   ```bash
   mkdir combo
   echo "user1:pass1" > combo/teste.txt
   echo "user2:pass2" >> combo/teste.txt
   ```

2. **Executar verificação**:
   ```bash
   python iptv_checker_optimized.py
   ```

3. **Seguir o menu interativo**:
   - Escolher "1" para arquivo local
   - Selecionar "teste.txt"
   - Inserir servidor: `http://meuservidor.com`
   - Pressionar Enter para iniciar

4. **Verificar resultados**:
   ```bash
   ls hits/
   cat hits/meuservidor_com.txt
   ```

## Formato de Saída

Os hits são salvos com informações completas:

```
━━━━━━━━━━━━━━━━━━━━━
✨ IPTV HIT ENCONTRADO ✨
━━━━━━━━━━━━━━━━━━━━━

🌐 HOST: http://servidor.com

👤 USUÁRIO: usuario123
🔑 SENHA: senha123

📅 EXPIRA: 15/12/2024 (30 dias)
🔗 CONEXÕES ATIVAS: 1
⚙️ CONEXÕES MÁXIMAS: 2
🛠️ STATUS: Active

🎵 M3U:
http://servidor.com/get.php?username=usuario123&password=senha123&type=m3u_plus

📺 CATEGORIAS:
SPORTS | MOVIES | NEWS | KIDS
```

## Dicas

- Use 20-40 requisições simultâneas para melhor estabilidade
- Timeout de 5-10 segundos é ideal para a maioria dos servidores
- Teste um servidor por vez para melhor precisão
- Mantenha combos organizados na pasta `combo`
- Verifique a pasta `hits` regularmente para resultados

## Suporte

Este verificador é otimizado para:
- Servidores IPTV com API padrão
- Combos no formato `usuario:senha`
- Verificação de credenciais ativas
- Extração de informações de conta e categorias