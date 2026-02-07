import discord
from discord.ext import commands
from discord import ui, ButtonStyle
import asyncio
from datetime import datetime
import re

# ========== CONFIGURAÇÃO ==========
STAFF_ROLES = [
    "👑┃OWNER"
    "👑┃LIDERANÇA"
    "👑┃CEO"
    "🔑┃ACESS"
    "👑┃Real XIT"
    "👤┃GERENTE"
    "👤┃RESP. ELITE"
    "📍┃RESP. CALL"
    "📍┃RESP. TICKET"
    "🎫┃RESP. E-MAIL"
    ":man_technologist:┃RESP. REC"
]

# ========== CLASSES DO SISTEMA DE SET ==========

class SetFinalizadoView(ui.View):
    """View após set ser aprovado/recusado - APENAS STAFF VÊ"""
    def __init__(self, fivem_id, game_nick, user_id):
        super().__init__(timeout=None)
        self.fivem_id = fivem_id
        self.game_nick = game_nick
        self.user_id = user_id
    
    @ui.button(label="✅ Concluir Pedido", style=ButtonStyle.green, custom_id="concluir_set")
    async def concluir_set(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            await interaction.response.send_message("❌ Apenas staff!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🏁 Pedido Concluído",
            description=f"Pedido concluído por {interaction.user.mention}",
            color=discord.Color.green()
        )
        
        self.clear_items()
        await interaction.message.edit(view=self)
        await interaction.channel.send(embed=embed)
    
    @ui.button(label="🗑️ Excluir Pedido", style=ButtonStyle.red, custom_id="excluir_set")
    async def excluir_set(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            await interaction.response.send_message("❌ Apenas staff!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            mensagem_pedido = interaction.message
            
            embed = discord.Embed(
                title="🗑️ Pedido Excluído",
                description=f"Pedido excluído por {interaction.user.mention}",
                color=discord.Color.red()
            )
            
            await interaction.channel.send(embed=embed)
            await mensagem_pedido.delete()
            
            print(f"✅ Pedido excluído - ID Fivem: {self.fivem_id}")
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para excluir mensagens!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao excluir: {e}", ephemeral=True)

class SetStaffView(ui.View):
    """View com botões para staff aprovar/recusar set"""
    def __init__(self, fivem_id, game_nick, user_id, discord_user):
        super().__init__(timeout=None)
        self.fivem_id = fivem_id
        self.game_nick = game_nick
        self.user_id = user_id
        self.discord_user = discord_user
    
    @ui.button(label="✅ Aprovar Set", style=ButtonStyle.green, custom_id="aprovar_set", row=0)
    async def aprovar_set(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            await interaction.response.send_message("❌ Apenas staff pode aprovar!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # VERIFICAR PERMISSÕES DO BOT
            bot_member = interaction.guild.me
            
            # Verificar permissão para gerenciar nicknames
            if not bot_member.guild_permissions.manage_nicknames:
                embed_erro = discord.Embed(
                    title="❌ PERMISSÃO NEGADA",
                    description=(
                        "O bot precisa da permissão **'Gerenciar Apelidos'**!\n\n"
                        "**Como resolver:**\n"
                        "1. Vá em **Configurações do Servidor**\n"
                        "2. **Cargos** → Cargo do Bot\n"
                        "3. Ative **'Gerenciar Apelidos'**\n"
                        "4. Salve as alterações"
                    ),
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed_erro, ephemeral=True)
                return
            
            # Verificar permissão para gerenciar cargos
            if not bot_member.guild_permissions.manage_roles:
                await interaction.followup.send(
                    "❌ O bot precisa da permissão **'Gerenciar Cargos'**!",
                    ephemeral=True
                )
                return
            
            # Buscar membro
            member = interaction.guild.get_member(self.user_id)
            
            if not member:
                await interaction.followup.send(f"❌ Usuário não encontrado! ID: `{self.user_id}`", ephemeral=True)
                return
            
            # 1. Criar nickname
            novo_nick = f"MEM | {self.game_nick} - {self.fivem_id}"
            if len(novo_nick) > 32:
                novo_nick = f"AV | {self.game_nick[:15]} - {self.fivem_id[:10]}"
            
            # 2. Mudar nickname
            await member.edit(nick=novo_nick)
            print(f"✅ Nickname alterado para: {novo_nick}")
            
            # 3. Remover cargo de visitante
            visitante_role = discord.utils.get(interaction.guild.roles, name="⏳┃Team REALXIT")
            if visitante_role and visitante_role in member.roles:
                await member.remove_roles(visitante_role)
                print(f"✅ Cargo '⏳┃Team REALXIT' removido de {member.name}")
            
            # 4. Dar cargo de membro
            membro_role = discord.utils.get(interaction.guild.roles, name="🫂┃Membro")
            if membro_role:
                await member.add_roles(membro_role)
                print(f"✅ Cargo '🫂┃Membro' adicionado a {member.name}")
            
            # Embed de aprovação
            embed_aprovado = discord.Embed(
                title="✅ SET APROVADO!",
                description=(
                    f"**👤 Discord:** {member.mention}\n"
                    f"**🎮 ID Fivem:** `{self.fivem_id}`\n"
                    f"**👤 Nick do Jogo:** `{self.game_nick}`\n"
                    f"**👑 Aprovado por:** {interaction.user.mention}\n"
                    f"**📅 Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                    f"✅ **Nickname alterado para:** `{novo_nick}`\n"
                    f"✅ **Cargo atualizado:** 🫂┃Membro"
                ),
                color=discord.Color.green()
            )
            
            if visitante_role and visitante_role in member.roles:
                embed_aprovado.description += f"\n✅ **Cargo removido:** ⏳┃Team REALXIT"
            
            # Remover botões
            self.clear_items()
            await interaction.message.edit(embed=embed_aprovado, view=self)
            
            # Adicionar view final
            finalizado_view = SetFinalizadoView(self.fivem_id, self.game_nick, self.user_id)
            await interaction.channel.send("**Controles Finais:**", view=finalizado_view)
            
            # Confirmação
            await interaction.followup.send(
                f"✅ Set de {member.mention} aprovado!\n"
                f"• Nickname: `{novo_nick}`\n"
                f"• Cargo: 🫂┃Membro",
                ephemeral=True
            )
            
            # DM para o usuário
            try:
                embed_dm = discord.Embed(
                    title="✅ SEU SET FOI APROVADO!",
                    description=(
                        f"Parabéns! Seu pedido de set foi aprovado por {interaction.user.mention}\n\n"
                        f"**📋 Detalhes:**\n"
                        f"• **Nickname:** `{novo_nick}`\n"
                        f"• **ID Fivem:** `{self.fivem_id}`\n"
                        f"• **Cargo:** 🫂┃Membro\n\n"
                        f"🎮 Bem-vindo ao servidor!"
                    ),
                    color=discord.Color.green()
                )
                await member.send(embed=embed_dm)
            except:
                pass
                
        except discord.Forbidden as e:
            print(f"❌ Erro de permissão: {e}")
            await interaction.followup.send(
                "❌ **ERRO DE PERMISSÃO!**\n\n"
                "Verifique:\n"
                "1. O bot tem 'Gerenciar Apelidos' e 'Gerenciar Cargos'\n"
                "2. O cargo do bot está ACIMA dos cargos que ele gerencia",
                ephemeral=True
            )
        except Exception as e:
            print(f"❌ Erro ao aprovar set: {type(e).__name__}: {e}")
            await interaction.followup.send(f"❌ Erro: {type(e).__name__}: {e}", ephemeral=True)
    
    @ui.button(label="❌ Recusar Set", style=ButtonStyle.red, custom_id="recusar_set", row=0)
    async def recusar_set(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.name in STAFF_ROLES for role in interaction.user.roles):
            await interaction.response.send_message("❌ Apenas staff pode recusar!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            mensagem_pedido = interaction.message
            
            embed_recusado = discord.Embed(
                title="❌ SET RECUSADO",
                description=(
                    f"**👤 Discord:** {self.discord_user.mention}\n"
                    f"**🎮 ID Fivem:** `{self.fivem_id}`\n"
                    f"**👤 Nick do Jogo:** `{self.game_nick}`\n"
                    f"**👑 Recusado por:** {interaction.user.mention}\n"
                    f"**📅 Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                ),
                color=discord.Color.red()
            )
            
            await interaction.channel.send(embed=embed_recusado)
            await mensagem_pedido.delete()
            
            await interaction.followup.send("✅ Set recusado e mensagem excluída!", ephemeral=True)
            print(f"✅ Set recusado - ID Fivem: {self.fivem_id}")
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para excluir mensagens!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)

class SetForm(ui.Modal, title="📝 Pedido de Set"):
    """Modal para coletar dados do set"""
    
    fivem_id = ui.TextInput(
        label="Digite seu ID do Jogo (Fivem):",
        placeholder="Ex: 2314",
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )
    
    game_nick = ui.TextInput(
        label="Digite seu Nick do Jogo:",
        placeholder="Ex: João silva",
        style=discord.TextStyle.short,
        required=True,
        max_length=32
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validar ID (apenas números)
            if not self.fivem_id.value.isdigit():
                error_msg = await interaction.followup.send(
                    "❌ ID deve conter apenas números!",
                    ephemeral=True
                )
                await asyncio.sleep(5)
                await error_msg.delete()
                return
            
            # Validar nick
            if not re.match(r'^[a-zA-Z0-9 _\-\.]+$', self.game_nick.value):
                error_msg = await interaction.followup.send(
                    "❌ Nick inválido! Use apenas letras, números, espaço, _, -, .",
                    ephemeral=True
                )
                await asyncio.sleep(5)
                await error_msg.delete()
                return
            
            # Encontrar canal de aprovação
            canal_aprovamento = discord.utils.get(interaction.guild.text_channels, name="aprovar-set")
            if not canal_aprovamento:
                await interaction.followup.send("❌ Canal #aprovar-set não encontrado!", ephemeral=True)
                return
            
            # Verificar se ID já existe
            async for message in canal_aprovamento.history(limit=100):
                if message.embeds and f"**🎮 ID Fivem:** `{self.fivem_id.value}`" in (message.embeds[0].description or ""):
                    await interaction.followup.send(f"❌ ID `{self.fivem_id.value}` já em uso!", ephemeral=True)
                    return
            
            # Criar embed
            embed = discord.Embed(
                title="🎮 NOVO PEDIDO DE SET",
                description=(
                    f"**👤 Discord:** {interaction.user.mention}\n"
                    f"**🆔 Discord ID:** `{interaction.user.id}`\n"
                    f"**🎮 ID Fivem:** `{self.fivem_id.value}`\n"
                    f"**👤 Nick do Jogo:** `{self.game_nick.value}`\n"
                    f"**📅 Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                    "**⏳ Status:** Aguardando aprovação"
                ),
                color=discord.Color.purple()
            )
            
            # Enviar para aprovação
            view = SetStaffView(self.fivem_id.value, self.game_nick.value, interaction.user.id, interaction.user)
            await canal_aprovamento.send(embed=embed, view=view)
            
            # Confirmação
            success_msg = await interaction.followup.send(
                f"✅ **Pedido enviado!**\nID: `{self.fivem_id.value}`\nNick: `{self.game_nick.value}`",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await success_msg.delete()
            
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)

class SetOpenView(ui.View):
    """View inicial - botão para pedir set"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Peça seu Set!", style=ButtonStyle.primary, custom_id="pedir_set")
    async def pedir_set(self, interaction: discord.Interaction, button: ui.Button):
        modal = SetForm()
        await interaction.response.send_modal(modal)

# ========== COG DO SISTEMA DE SET ==========

class SetsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Módulo Sets carregado!")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_set(self, ctx):
        """Configura o painel de pedido de set"""
        
        embed = discord.Embed(
            title="🎮 **PEÇA SEU SET AQUI!**",
            description=(
                "Clique no botão abaixo e peça seu\n"
                "aprovamento para receber seu set\n"
                "personalizado no servidor.\n\n"
                "**📌 Instruções:**\n"
                "1. Clique em **'Peça seu Set!'**\n"
                "2. Digite seu **ID do Fivem**\n"
                "3. Digite seu **Nick do Jogo**\n"
                "4. Aguarde aprovação da equipe\n\n"
            ),
            color=discord.Color.purple()
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/1421981847201644635/1424930657074941983/image.png?ex=69888ed6&is=69873d56&hm=876797039575c7c96db986c770db50fd8fe8236b40f50e841fbfb9014173056f")
        embed.set_footer(text="Sistema automático • Setagem!")
        
        view = SetOpenView()
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def check_id(self, ctx, *, fivem_id: str):
        """Verifica se um ID Fivem já está em uso"""
        canal = discord.utils.get(ctx.guild.text_channels, name="aprovar-set")
        if not canal:
            await ctx.send("❌ Canal #aprovar-set não encontrado!")
            return
        
        if not fivem_id.isdigit():
            await ctx.send("❌ ID deve conter apenas números!")
            return
        
        encontrado = False
        async for message in canal.history(limit=100):
            if message.embeds and f"**🎮 ID Fivem:** `{fivem_id}`" in (message.embeds[0].description or ""):
                await ctx.send(f"❌ ID `{fivem_id}` já em uso! [Ver pedido]({message.jump_url})")
                encontrado = True
                break
        
        if not encontrado:
            await ctx.send(f"✅ ID `{fivem_id}` não está em uso!")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sets_pendentes(self, ctx):
        """Mostra pedidos pendentes"""
        canal = discord.utils.get(ctx.guild.text_channels, name="aprovar-set")
        if not canal:
            await ctx.send("❌ Canal #aprovamento não encontrado!")
            return
        
        pedidos = []
        async for message in canal.history(limit=50):
            if message.embeds and "Aguardando aprovação" in (message.embeds[0].description or ""):
                pedidos.append(message)
        
        if not pedidos:
            await ctx.send("✅ Nenhum pedido pendente!")
            return
        
        embed = discord.Embed(
            title="📋 Pedidos Pendentes",
            description=f"Total: **{len(pedidos)}** pedidos",
            color=discord.Color.blue()
        )
        
        for i, msg in enumerate(pedidos[:5], 1):
            desc = msg.embeds[0].description or ""
            id_match = re.search(r'\*\*🎮 ID Fivem:\*\* `([^`]+)`', desc)
            nick_match = re.search(r'\*\*👤 Nick do Jogo:\*\* `([^`]+)`', desc)
            
            embed.add_field(
                name=f"Pedido #{i}",
                value=f"**ID:** `{id_match.group(1) if id_match else '?'}`\n**Nick:** `{nick_match.group(1) if nick_match else '?'}`",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remover_visitante(self, ctx, member: discord.Member):
        """Remove manualmente o cargo de ⏳┃Team REALXIT"""
        try:
            visitante_role = discord.utils.get(ctx.guild.roles, name="⏳┃Team REALXIT")
            if not visitante_role:
                await ctx.send("❌ Cargo '⏳┃Team REALXIT' não encontrado!")
                return
            
            if visitante_role in member.roles:
                await member.remove_roles(visitante_role)
                await ctx.send(f"✅ Cargo '⏳┃Team REALXIT' removido de {member.mention}")
            else:
                await ctx.send(f"❌ {member.mention} não possui o cargo '⏳┃Team REALXIT'")
                
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para modificar cargos!")
        except Exception as e:
            await ctx.send(f"❌ Erro: {e}")

async def setup(bot):
    await bot.add_cog(SetsCog(bot))
    print("✅ Sistema de Sets configurado!")
