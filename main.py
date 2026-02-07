from datetime import datetime
import discord
from discord.ext import commands
import os
import sys
import asyncio
import aiohttp
from aiohttp import web

# ==================== KEEP-ALIVE SIMPLES ====================
class KeepAliveServer:
    def __init__(self):
        self.app = None
        self.runner = None
        self.site = None
    
    async def start_simple(self):
        """Inicia um servidor web simples na porta 10000"""
        try:
            self.app = web.Application()
            
            async def handle(request):
                return web.Response(text="🤖 Bot Discord Online")
            
            async def handle_health(request):
                return web.json_response({
                    "status": "online",
                    "timestamp": datetime.now().isoformat()
                })
            
            self.app.router.add_get('/', handle)
            self.app.router.add_get('/health', handle_health)
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Usar porta 10000 para evitar conflito
            self.site = web.TCPSite(self.runner, '0.0.0.0', 10000)
            await self.site.start()
            
            print(f"🌐 Keep-alive iniciado na porta 10000")
            print(f"📊 Health check: https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')}:10000/health")
            
        except Exception as e:
            print(f"⚠️ Não foi possível iniciar keep-alive: {e}")
            print("⚠️ Bot continuará sem servidor web...")
    
    async def stop(self):
        """Para o servidor web"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

# ==================== BOT DISCORD ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
keep_alive = KeepAliveServer()

# ==================== EVENTO DE ENTRADA DE MEMBRO ====================
@bot.event
async def on_member_join(member: discord.Member):
    """Atribui cargo automático quando alguém entra"""
    print(f"👤 {member.name} entrou no servidor!")
    
    try:
        # Buscar cargo "𝐕𝐢𝐬𝐢𝐭𝐚𝐧𝐭𝐞"
        visitante_role = discord.utils.get(member.guild.roles, name="𝐕𝐢𝐬𝐢𝐭𝐚𝐧𝐭𝐞")
        
        if not visitante_role:
            print("❌ Cargo '𝐕𝐢𝐬𝐢𝐭𝐚𝐧𝐭𝐞' não encontrado!")
            
            # Tentar criar automaticamente
            try:
                visitante_role = await member.guild.create_role(
                    name="𝐕𝐢𝐬𝐢𝐭𝐚𝐧𝐭𝐞",
                    color=discord.Color.light_grey(),
                    reason="Criado automaticamente pelo sistema de boas-vindas"
                )
                print(f"✅ Cargo '𝐕𝐢𝐬𝐢𝐭𝐚𝐧𝐭𝐞' criado automaticamente!")
            except discord.Forbidden:
                print("❌ Sem permissão para criar cargo!")
                return
            except Exception as e:
                print(f"❌ Erro ao criar cargo: {e}")
                return
                
        # Dar o cargo ao membro
        await member.add_roles(visitante_role)
        print(f"✅ Cargo '𝐕𝐢𝐬𝐢𝐭𝐚𝐧𝐭𝐞' atribuído a {member.name}")
        
        # Enviar mensagem de boas-vindas
        try:
            canal_entrada = discord.utils.get(member.guild.text_channels, name="🚪entrada")
            
            if not canal_entrada:
                canal_entrada = discord.utils.get(member.guild.text_channels, name="entrada")
            
            if not canal_entrada:
                for channel in member.guild.text_channels:
                    if channel.permissions_for(member.guild.me).send_messages:
                        canal_entrada = channel
                        break
            
            if canal_entrada:
                embed = discord.Embed(
                    title=f"👋 Bem-vindo(a), {member.name}!",
                    description=(
                        f"Seja muito bem-vindo(a) ao **{member.guild.name}**!\n\n"
                        f"👤 **Total de membros:** {member.guild.member_count}\n\n"
                        f"💡 **Para fazer seu set:**\n"
                        f"1. Vá para #Pedir set!\n"
                        f"2. Clique em 'Peça seu Set!'\n"
                        f"3. Digite seu ID do FiveM\n"
                        f"4. E aguarde aprovação da staff!"
                    ),
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                embed.set_footer(text="Seja Bem-vindo!, Esperamos que goste!")
                
                await canal_entrada.send(embed=embed)
                print(f"✅ Mensagem de boas-vindas enviada em #{canal_entrada.name}")
                
        except Exception as e:
            print(f"⚠️ Não foi possível enviar mensagem de boas-vindas: {e}")
        
        print(f"✅ {member.name} recebeu cargo automático")
        
    except discord.Forbidden:
        print(f"❌ Sem permissão para adicionar cargos a {member.name}")
    except Exception as e:
        print(f"❌ Erro no sistema de boas-vindas: {type(e).__name__}: {e}")

# ==================== CARREGAR MÓDULOS ====================
async def load_cogs():
    """Carrega módulos adicionais"""
    print("=" * 50)
    print("🔄 CARREGANDO MÓDULOS...")
    
    # Lista de módulos
    cogs = [
        'modules.sets',
        'modules.cargos',
    ]
    
    carregados = 0
    for cog in cogs:
        print(f"\n🔍 Tentando: {cog}")
        try:
            await bot.load_extension(cog)
            print(f"✅ '{cog}' carregado!")
            carregados += 1
        except ModuleNotFoundError:
            print(f"⚠️ Módulo não encontrado")
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
        except Exception as e:
            print(f"❌ Erro: {type(e).__name__}: {e}")
    
    print(f"\n📊 {carregados}/{len(cogs)} módulos carregados")
    print("=" * 50)
    return carregados > 0

# ==================== EVENTOS ====================
@bot.event
async def on_ready():
    print(f'✅ Bot logado como: {bot.user}')
    print(f'🆔 ID: {bot.user.id}')
    print(f'📡 Ping: {round(bot.latency * 1000)}ms')
    print(f'🏠 Servidores: {len(bot.guilds)}')
    print('🚀 Bot pronto!')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servidor(es) | !help"
        )
    )
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados")
    except:
        print("⚠️ Sem comandos slash para sincronizar")

# ==================== COMANDOS ====================
@bot.command()
async def ping(ctx):
    """Mostra latência do bot"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: **{latency}ms**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
async def status(ctx):
    """Mostra status do bot"""
    embed = discord.Embed(
        title="🤖 Status do Bot",
        color=discord.Color.green()
    )
    
    embed.add_field(name="🏷️ Nome", value=bot.user.name, inline=True)
    embed.add_field(name="🆔 ID", value=bot.user.id, inline=True)
    embed.add_field(name="📡 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="🏠 Servidores", value=len(bot.guilds), inline=True)
    
    total_members = sum(len(g.members) for g in bot.guilds)
    embed.add_field(name="👤 Membros", value=total_members, inline=True)
    
    loaded_cogs = list(bot.cogs.keys())
    embed.add_field(
        name="📦 Módulos", 
        value="\n".join([f"• {cog}" for cog in loaded_cogs]) if loaded_cogs else "Nenhum",
        inline=False
    )
    
    embed.set_footer(text="Online 24/7")
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx):
    """Recarrega módulos"""
    await load_cogs()
    await ctx.send("✅ Módulos recarregados!")

# ==================== TRATAMENTO DE ERROS ====================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Comando não encontrado. Use `!help`", delete_after=5)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Sem permissão!", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argumentos faltando! Use: `!{ctx.command.name} {ctx.command.signature}`", delete_after=5)
    else:
        print(f"Erro: {error}")

# ==================== INICIALIZAÇÃO ====================
async def main():
    """Função principal"""
    print("🚀 Iniciando bot Discord...")
    print("=" * 50)
    
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ DISCORD_TOKEN não encontrado!")
        print("Configure no Render: Environment → DISCORD_TOKEN")
        sys.exit(1)
    
    # Iniciar keep-alive em porta diferente
    try:
        print("🌐 Iniciando servidor keep-alive...")
        await keep_alive.start_simple()
    except Exception as e:
        print(f"⚠️ Erro no keep-alive: {e}")
        print("⚠️ Continuando sem servidor web...")
    
    # Carregar módulos
    await load_cogs()
    
    # Iniciar bot
    print("🔗 Conectando ao Discord...")
    try:
        await bot.start(TOKEN)
    finally:
        # Garantir que o servidor web seja parado
        await keep_alive.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
