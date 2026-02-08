import discord
from discord.ext import commands
from discord import ui, ButtonStyle
import asyncio
from datetime import datetime
import re

# ========== CONFIGURAÇÃO COM SEUS CARGOS REAIS ==========
# ORDEM DECRESCENTE (do maior para o menor)
ORDEM_DECRESCENTE = [
    "👑┃OWNER",           # 1 - MAIOR
    "👑┃CEO",             # 2
    "👑┃Real XIT",        # 3
    "💰┃Doações GANG $",  # 4
    "👤┃GERENTE",         # 5
    "👤┃RESP. ELITE",     # 6
    "🎫┃RESP. E-MAIL",    # 7
    "👤┃ELITE",           # 8 - LIMITE: daqui pra CIMA sem ID
    "📸┃STREAMER",        # 9 - daqui pra BAIXO com ID
    "🚀┃RealXit Booster", # 10
    "🫂┃Membro",          # 11
    "🫱🏻‍🫲🏻┃Parceiro",    # 12
    "⏳┃Team REALXIT",     # 13
    "👼🏻┃FILHO DO PROFESSOR"  # 14 - MENOR
]

# Templates de nickname
NICKNAME_TEMPLATES = {
    # CARGOS ACIMA DE "👤┃ELITE" (SEM ID)
    "👑┃OWNER": "OWNER | {name}",
    "👑┃CEO": "CEO | {name}",
    "👑┃Real XIT": "Real XIT | {name}",
    "💰┃Doações GANG $": "DOAÇÃO | {name}",
    "👤┃GERENTE": "GER | {name}",
    "👤┃RESP. ELITE": "RESP ELITE | {name}",
    "🎫┃RESP. E-MAIL": "EMAIL | {name}",
    "👤┃ELITE": "ELITE | {name}",
    
    # CARGOS ABAIXO DE "👤┃ELITE" (COM ID)
    "📸┃STREAMER": "STREAM | {name} - {id}",
    "🚀┃RealXit Booster": "BOOSTER | {name} - {id}",
    "🫂┃Membro": "MEM | {name} - {id}",
    "🫱🏻‍🫲🏻┃Parceiro": "PARCEIRO | {name} - {id}",
    "⏳┃Team REALXIT": "TEAM | {name} - {id}",
    "👼🏻┃FILHO DO PROFESSOR": "FILHO | {name} - {id}",
}

# Cargos que podem usar o sistema (staff)
STAFF_ROLES = [
    "👑┃OWNER", "👑┃CEO", "👑┃Real XIT", 
    "💰┃Doações GANG $", "👤┃GERENTE", 
    "👤┃RESP. ELITE", "🎫┃RESP. E-MAIL"
]

# ========== FUNÇÕES AUXILIARES ==========
def buscar_usuario_por_fivem_id(guild: discord.Guild, fivem_id: str) -> discord.Member:
    """Busca usuário pelo ID do FiveM no nickname"""
    for member in guild.members:
        if member.nick:
            # Padrão 1: " - 26046" no final
            if member.nick.endswith(f" - {fivem_id}"):
                return member
            
            # Padrão 2: "-26046" no final
            if member.nick.endswith(f"-{fivem_id}"):
                return member
            
            # Padrão 3: contém "26046" em qualquer lugar
            if fivem_id in member.nick:
                # Verificar se são os últimos números
                match = re.search(rf'(\D|^){fivem_id}(\D|$)', member.nick)
                if match:
                    return member
    
    return None

def extrair_parte_nickname(nickname: str):
    """Extrai a primeira parte do nickname (antes do ' - ')"""
    if not nickname:
        return "User"
    
    # Padrão: "PREFIX | Nome - ID" ou apenas "Nome - ID"
    parts = nickname.split(' - ')
    if len(parts) > 1:
        primeira_parte = parts[0]
        # Remover prefixo se existir (ex: "MEM | ")
        if ' | ' in primeira_parte:
            primeira_parte = primeira_parte.split(' | ')[1]
        return primeira_parte.strip()
    
    # Se não tem traço, pode ser apenas o nome
    if ' | ' in nickname:
        return nickname.split(' | ')[1].strip()
    
    return nickname.strip()

def extrair_id_fivem(nickname: str):
    """Extrai ID do FiveM do nickname (números após o último ' - ')"""
    if not nickname:
        return None
    
    # Procurar padrão: " - 123456"
    match = re.search(r' - (\d+)$', nickname)
    if match:
        return match.group(1)
    
    # Tentar padrão alternativo
    match = re.search(r'-(\d+)$', nickname)
    if match:
        return match.group(1)
    
    return None

def deve_usar_id_fivem(cargo_nome: str) -> bool:
    """Verifica se o cargo deve usar ID do FiveM no nickname"""
    try:
        index_elite = ORDEM_DECRESCENTE.index("👤┃ELITE")
        index_cargo = ORDEM_DECRESCENTE.index(cargo_nome)
        
        # Se o cargo está ABAIXO de Elite na lista, usa ID
        return index_cargo > index_elite
    except ValueError:
        return False  # Se não encontrar o cargo, não usa ID

async def atualizar_nickname(member: discord.Member):
    """Atualiza nickname seguindo as regras específicas"""
    try:
        # Verificar permissões
        if not member.guild.me.guild_permissions.manage_nicknames:
            return False
        
        # Extrair partes do nickname atual
        nickname_atual = member.nick or member.name
        parte_nome = extrair_parte_nickname(nickname_atual)
        id_fivem = extrair_id_fivem(nickname_atual)
        
        # Encontrar cargo principal (mais alto na hierarquia)
        cargo_principal = None
        for cargo_nome in ORDEM_DECRESCENTE:
            if discord.utils.get(member.roles, name=cargo_nome):
                cargo_principal = cargo_nome
                break
        
        if not cargo_principal or cargo_principal not in NICKNAME_TEMPLATES:
            return False
        
        # Gerar novo nickname
        template = NICKNAME_TEMPLATES[cargo_principal]
        
        if deve_usar_id_fivem(cargo_principal):
            # Precisa de ID do FiveM
            if not id_fivem:
                id_fivem = "000000"  # Placeholder se não tiver
            novo_nick = template.format(name=parte_nome, id=id_fivem)
        else:
            # Não usa ID do FiveM
            novo_nick = template.format(name=parte_nome)
        
        # Limitar a 32 caracteres
        if len(novo_nick) > 32:
            novo_nick = novo_nick[:32]
        
        # Aplicar se for diferente
        if member.nick != novo_nick:
            await member.edit(nick=novo_nick)
            print(f"✅ Nickname atualizado: {member.name} -> {novo_nick}")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao atualizar nickname: {e}")
    
    return False

# ========== SISTEMA CLEAN DE CARGO ==========
class CargoSelectView(ui.View):
    """View simples para selecionar cargo"""
    def __init__(self, member: discord.Member, action: str):
        super().__init__(timeout=60)
        self.member = member
        self.action = action  # "add" ou "remove"
        
        # Opções de cargo (seus cargos reais)
        options = []
        cargos_disponiveis = [
            ("👑┃OWNER", "Dono"),
            ("👑┃CEO", "CEO"),
            ("👑┃Real XIT", "Real XIT"),
            ("💰┃Doações GANG $", "Doações"),
            ("👤┃GERENTE", "Gerente"),
            ("👤┃RESP. ELITE", "Resp. Elite"),
            ("🎫┃RESP. E-MAIL", "Resp. Email"),
            ("👤┃ELITE", "Elite"),
            ("📸┃STREAMER", "Streamer"),
            ("🚀┃RealXit Booster", "Booster"),
            ("🫂┃Membro", "Membro"),
            ("🫱🏻‍🫲🏻┃Parceiro", "Parceiro"),
            ("⏳┃Team REALXIT", "Team REALXIT"),
            ("👼🏻┃FILHO DO PROFESSOR", "Filho do Professor"),
        ]
        
        for cargo_nome, desc in cargos_disponiveis:
            options.append(
                discord.SelectOption(
                    label=cargo_nome,
                    description=desc
                )
            )
        
        self.select = ui.Select(
            placeholder="Selecione o cargo...",
            options=options,
            custom_id="cargo_select"
        )
        self.select.callback = self.on_select
        self.add_item(self.select)
    
    async def on_select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        cargo_nome = self.select.values[0]
        cargo = discord.utils.get(interaction.guild.roles, name=cargo_nome)
        
        if not cargo:
            msg = await interaction.followup.send("❌ Cargo não encontrado!", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        try:
            if self.action == "add":
                await self.member.add_roles(cargo)
                mensagem = f"✅ Cargo `{cargo.name}` adicionado para {self.member.mention}"
            else:
                await self.member.remove_roles(cargo)
                mensagem = f"✅ Cargo `{cargo.name}` removido de {self.member.mention}"
            
            # Atualizar nickname
            await atualizar_nickname(self.member)
            
            # Enviar mensagem temporária
            msg = await interaction.followup.send(mensagem, ephemeral=False)
            await asyncio.sleep(5)
            await msg.delete()
            
            # Deletar a mensagem com o select também
            await interaction.delete_original_response()
            
        except discord.Forbidden:
            msg = await interaction.followup.send("❌ Sem permissão!", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
        except Exception as e:
            msg = await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()

# ========== MODAL SIMPLES ==========
class SimpleCargoModal(ui.Modal, title="🎯 Gerenciar Cargo"):
    """Modal simples para gerenciar cargo"""
    
    usuario_input = ui.TextInput(
        label="Usuário (@nome ou número do FiveM):",
        placeholder="Ex: @João ou 26046",
        required=True
    )
    
    def __init__(self, action: str):
        super().__init__()
        self.action = action  # "add" ou "remove"
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Verificar se é staff
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            msg = await interaction.followup.send("❌ Apenas staff pode usar!", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        # Encontrar usuário
        member = None
        input_text = self.usuario_input.value
        
        try:
            # 1. Se for menção (@usuário)
            if "<@" in input_text:
                user_id = input_text.replace("<@", "").replace(">", "").replace("!", "")
                member = interaction.guild.get_member(int(user_id))
            
            # 2. Se for apenas números (ID do FiveM)
            elif input_text.isdigit():
                # Primeiro, buscar pelo ID do FiveM no nickname
                member = buscar_usuario_por_fivem_id(interaction.guild, input_text)
                
                # Se não encontrou, buscar pelo ID do Discord
                if not member:
                    try:
                        member = interaction.guild.get_member(int(input_text))
                    except:
                        pass
            
            # 3. Se for texto (nome)
            else:
                # Buscar por nome no nickname primeiro
                for guild_member in interaction.guild.members:
                    if guild_member.nick and input_text.lower() in guild_member.nick.lower():
                        member = guild_member
                        break
                
                # Se não encontrou no nickname, buscar no nome
                if not member:
                    for guild_member in interaction.guild.members:
                        if input_text.lower() in guild_member.name.lower():
                            member = guild_member
                            break
            
            if not member:
                # Mostrar mensagem mais útil
                embed = discord.Embed(
                    title="❌ Usuário não encontrado!",
                    description=(
                        f"Não encontrei nenhum usuário com: `{input_text}`\n\n"
                        "**Formas de buscar:**\n"
                        "1. **Menção**: `@João`\n"
                        "2. **ID do FiveM**: `26046` (deve estar no nickname)\n"
                        "3. **Nome**: `João` ou parte do nome\n\n"
                        "**📌 Exemplo de nickname com ID:**\n"
                        "`MEM | João - 26046`"
                    ),
                    color=discord.Color.red()
                )
                msg = await interaction.followup.send(embed=embed, ephemeral=True)
                await asyncio.sleep(8)
                await msg.delete()
                return
            
            # Mostrar view para selecionar cargo
            view = CargoSelectView(member, self.action)
            
            # Verificar se tem ID do FiveM no nickname
            id_fivem = extrair_id_fivem(member.nick or member.name)
            
            # Criar embed simples
            embed = discord.Embed(
                title=f"{'➕ Adicionar' if self.action == 'add' else '➖ Remover'} Cargo",
                description=(
                    f"**Usuário:** {member.mention}\n"
                    f"**Nickname atual:** `{member.nick or member.name}`\n"
                    f"**ID FiveM:** `{id_fivem or 'Não encontrado'}`\n\n"
                    f"Selecione o cargo abaixo:"
                ),
                color=discord.Color.blue() if self.action == "add" else discord.Color.red()
            )
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro!",
                description=f"Ocorreu um erro: `{str(e)}`",
                color=discord.Color.red()
            )
            msg = await interaction.followup.send(embed=embed, ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()

# ========== VIEW DO PAINEL ==========
class CleanCargoView(ui.View):
    """View clean do painel de cargos"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="➕ Add Cargo", style=ButtonStyle.green, emoji="➕", custom_id="add_cargo_clean")
    async def add_cargo(self, interaction: discord.Interaction, button: ui.Button):
        # Verificar staff
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            msg = await interaction.response.send_message("❌ Apenas staff!", ephemeral=True)
            return
        
        modal = SimpleCargoModal("add")
        await interaction.response.send_modal(modal)
    
    @ui.button(label="➖ Rem Cargo", style=ButtonStyle.red, emoji="➖", custom_id="remove_cargo_clean")
    async def remove_cargo(self, interaction: discord.Interaction, button: ui.Button):
        # Verificar staff
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            msg = await interaction.response.send_message("❌ Apenas staff!", ephemeral=True)
            return
        
        modal = SimpleCargoModal("remove")
        await interaction.response.send_modal(modal)

# ========== COG PRINCIPAL ==========
class CargosCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Sistema de Cargos carregado!")
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Atualiza nickname quando cargo muda"""
        if before.roles != after.roles:
            await asyncio.sleep(1)
            await atualizar_nickname(after)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Carrega view persistente"""
        self.bot.add_view(CleanCargoView())
        print("✅ View de cargos carregada")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_cargos(self, ctx):
        """Cria painel clean de cargos"""
        
        embed = discord.Embed(
            title="⚙️ SISTEMA DE CARGOS",
            description=(
                "**Como funciona:**\n"
                "1. Clique em Add ou Rem\n"
                "2. Digite @usuário ou ID do FiveM\n"
                "3. Selecione o cargo\n"
                "✅ Nickname atualiza automaticamente\n\n"
                "**📌 Regras de Nickname:**\n"
                "• **Cargos ALTOS** (👤┃ELITE pra cima): `CARGO | Nome`\n"
                "• **Cargos BAIXOS** (👤┃ELITE pra baixo): `CARGO | Nome - ID`\n"
                "• Apenas staff pode usar"
            ),
            color=discord.Color.blue()
        )
        
        # Adicionar exemplos
        embed.add_field(
            name="🎯 Exemplos de Nickname",
            value=(
                "**Sem ID (cargos altos):**\n"
                "• OWNER | João\n"
                "• GER | Maria\n"
                "• ELITE | Pedro\n\n"
                "**Com ID (cargos baixos):**\n"
                "• MEM | Ana - 26046\n"
                "• TEAM | Carlos - 12345"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👑 Staff Permitido",
            value="\n".join(STAFF_ROLES[:5]) + "\n...",
            inline=False
        )
        
        embed.set_footer(text="Sistema Clean • Mensagens auto-deletam em 5s")
        
        view = CleanCargoView()
        
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()
    
    @commands.command()
    async def fixnick(self, ctx, member: discord.Member = None):
        """Corrige nickname manualmente"""
        if member is None:
            member = ctx.author
        
        success = await atualizar_nickname(member)
        
        if success:
            msg = await ctx.send(f"✅ Nickname de {member.mention} corrigido!")
            await asyncio.sleep(5)
            await msg.delete()
        else:
            msg = await ctx.send(f"❌ Não foi possível corrigir o nickname")
            await asyncio.sleep(5)
            await msg.delete()

async def setup(bot):
    await bot.add_cog(CargosCog(bot))
