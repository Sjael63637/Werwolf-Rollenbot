import discord
from discord.ext import commands
from discord import app_commands
import random
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

rollen_pool = []
rollen_status = {}
vergebene_rollen = {}

def ist_admin_oder_spielleiter(interaction: discord.Interaction):
    return (
        interaction.user.guild_permissions.administrator or
        discord.utils.get(interaction.user.roles, name="Spielleiter")
    )

@bot.event
async def on_ready():
    print(f"Bot ist bereit: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash-Befehle synchronisiert: {len(synced)} Befehle")
    except Exception as e:
        print(f"Fehler beim Sync: {e}")

@bot.tree.command(name="rolle_hinzufügen", description="Fügt eine neue Rolle zur Liste hinzu.")
async def rolle_hinzufügen(interaction: discord.Interaction, name: str):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen Rollen hinzufügen.", ephemeral=True)
        return

    if name in rollen_pool:
        await interaction.response.send_message(f"Die Rolle '{name}' existiert bereits.", ephemeral=True)
        return
    rollen_pool.append(name)
    rollen_status[name] = True
    await interaction.response.send_message(f"Rolle '{name}' hinzugefügt und aktiviert.", ephemeral=True)

@bot.tree.command(name="rolle_entfernen", description="Entfernt eine Rolle aus der Liste.")
async def rolle_entfernen(interaction: discord.Interaction, name: str):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen Rollen entfernen.", ephemeral=True)
        return

    if name not in rollen_pool:
        await interaction.response.send_message(f"Die Rolle '{name}' existiert nicht.", ephemeral=True)
        return
    rollen_pool.remove(name)
    rollen_status.pop(name, None)
    await interaction.response.send_message(f"Rolle '{name}' entfernt.", ephemeral=True)

@bot.tree.command(name="rolle_aktivieren", description="Aktiviere eine Rolle aus der Liste.")
async def rolle_aktivieren(interaction: discord.Interaction):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen Rollen aktivieren.", ephemeral=True)
        return

    inaktive = [rolle for rolle in rollen_pool if not rollen_status.get(rolle)]
    if not inaktive:
        await interaction.response.send_message("Alle Rollen sind bereits aktiv.", ephemeral=True)
        return

    class AktivierungsSelect(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=r) for r in inaktive]
            super().__init__(placeholder="Wähle eine Rolle", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            rolle = self.values[0]
            rollen_status[rolle] = True
            await interaction.response.send_message(f"Rolle '{rolle}' wurde aktiviert.", ephemeral=True)

    class AktivierungsView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
            self.add_item(AktivierungsSelect())

    await interaction.response.send_message("Wähle eine Rolle zum Aktivieren:", view=AktivierungsView(), ephemeral=True)

@bot.tree.command(name="rolle_deaktivieren", description="Deaktiviere eine Rolle aus der Liste.")
async def rolle_deaktivieren(interaction: discord.Interaction):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen Rollen deaktivieren.", ephemeral=True)
        return

    aktive = [rolle for rolle in rollen_pool if rollen_status.get(rolle)]
    if not aktive:
        await interaction.response.send_message("Alle Rollen sind bereits deaktiviert.", ephemeral=True)
        return

    class DeaktivierungsSelect(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=r) for r in aktive]
            super().__init__(placeholder="Wähle eine Rolle", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            rolle = self.values[0]
            rollen_status[rolle] = False
            await interaction.response.send_message(f"Rolle '{rolle}' wurde deaktiviert.", ephemeral=True)

    class DeaktivierungsView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
            self.add_item(DeaktivierungsSelect())

    await interaction.response.send_message("Wähle eine Rolle zum Deaktivieren:", view=DeaktivierungsView(), ephemeral=True)

@bot.tree.command(name="rollenvergabe", description="Erhalte deine geheime Rolle.")
async def rollenvergabe(interaction: discord.Interaction):
    user = interaction.user

    if user.id in vergebene_rollen:
        await interaction.response.send_message("Du hast bereits eine Rolle erhalten.", ephemeral=True)
        return

    aktive_rollen = [r for r in rollen_pool if rollen_status.get(r)]
    verbleibende = [r for r in aktive_rollen if r not in vergebene_rollen.values()]

    if not verbleibende:
        await interaction.response.send_message("Alle Rollen wurden bereits vergeben.", ephemeral=True)
        return

    zugewiesen = random.choice(verbleibende)
    vergebene_rollen[user.id] = zugewiesen

    await interaction.response.send_message(f"Hier siehst du deine Rolle für dieses Spiel:\n**{zugewiesen}**", ephemeral=True)

@bot.tree.command(name="rolle_reset", description="Setzt alle vergebenen Rollen zurück.")
async def rolle_reset(interaction: discord.Interaction):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen diesen Befehl nutzen.", ephemeral=True)
        return

    vergebene_rollen.clear()
    await interaction.response.send_message("Alle vergebenen Rollen wurden zurückgesetzt.", ephemeral=True)

@bot.tree.command(name="rollen_deaktivieren_alle", description="Deaktiviert alle Rollen auf einmal.")
async def rollen_deaktivieren_alle(interaction: discord.Interaction):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen diesen Befehl nutzen.", ephemeral=True)
        return

    for rolle in rollen_pool:
        rollen_status[rolle] = False

    await interaction.response.send_message("Alle Rollen wurden deaktiviert.", ephemeral=True)

@bot.tree.command(name="rollen_liste", description="Zeigt, wer welche Rolle erhalten hat.")
async def rollen_liste(interaction: discord.Interaction):
    if not ist_admin_oder_spielleiter(interaction):
        await interaction.response.send_message("Nur Admins oder Spielleiter dürfen die Rollenliste sehen.", ephemeral=True)
        return

    if not vergebene_rollen:
        await interaction.response.send_message("Noch keine Rollen wurden vergeben.", ephemeral=True)
        return

    nachricht = "**Vergebene Rollen:**\n"
    for user_id, rolle in vergebene_rollen.items():
        member = await interaction.guild.fetch_member(user_id)
        nachricht += f"- {member.display_name}: {rolle}\n"

    await interaction.response.send_message(nachricht, ephemeral=True)

# Bot starten
keep_alive()
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
