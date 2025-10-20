import discord
from discord.ext import commands, tasks
import asyncio
import random
import dotenv
import os
from supabase import create_client
dotenv.load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_client = create_client(supabase_url, supabase_key)

def fmt(n):
    return f"{n:,}"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    await bot.change_presence(activity=discord.CustomActivity("Counting Cards!"))
    update_status.start()

@tasks.loop(seconds=12)
async def update_status():
    await bot.wait_until_ready()
    statuses = [
        f"Playing with {fmt(len(bot.users))} users!",
        "Counting Cards!",
        "High stakes, high rewards!",
        "Cashing out big wins!",
        "Dealing the deck!",
    ]
    for status in statuses:
        await bot.change_presence(activity=discord.CustomActivity(status))
        await asyncio.sleep(12)

@bot.tree.command(name="balance", description="Check your balance")
async def balance_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    # Fetch user balance from Supabase
    # Use the latest supabase-py API response handling
    response = supabase_client.table("users").select("balance").eq("id", user_id).execute()
    if response.data and len(response.data) > 0:
        balance = response.data[0]["balance"]
        embed = discord.Embed(title="💰 Your Balance", description=f"You have <:coin:1429548357206151401>{fmt(balance)} in your account.", color=discord.Color.from_str("#00A8B5"))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    # If no user found, create new user with balance 0
    insert_response = supabase_client.table("users").insert({"id": user_id, "balance": 0}).execute()
    if insert_response.data:
        embed = discord.Embed(title="💰 Your Balance", description=f"You have <:coin:1429548357206151401>{fmt(balance)} in your account.", color=discord.Color.from_str("#00A8B5"))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    # If still no data, show error
    await interaction.response.send_message("Error fetching or creating your balance. Please contact an admin.")

@bot.tree.command(name="daily", description="Claim your daily reward")
async def daily_command(interaction: discord.Interaction):
    import datetime
    user_id = interaction.user.id
    # Fetch user balance and last_daily from Supabase
    response = supabase_client.table("users").select("balance", "last_daily").eq("id", user_id).execute()
    now = datetime.datetime.utcnow()
    daily_reward = 500
    if response.data and len(response.data) > 0:
        user = response.data[0]
        balance = user["balance"]
        last_daily = user.get("last_daily")
        if last_daily:
            # Parse last_daily as datetime
            try:
                last_daily_dt = datetime.datetime.fromisoformat(last_daily.replace("Z", "+00:00"))
            except Exception:
                last_daily_dt = None
            if last_daily_dt and (now - last_daily_dt).total_seconds() < 86400:
                remaining = 86400 - (now - last_daily_dt).total_seconds()
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                embed = discord.Embed(title="⏳ Daily Reward", description=f"You can claim your next daily reward in ⌚{hours}h {minutes}m.", color=discord.Color.brand_red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        new_balance = balance + daily_reward
        supabase_client.table("users").update({"balance": new_balance, "last_daily": now.isoformat()}).eq("id", user_id).execute()
        embed = discord.Embed(title="✅ Daily Reward Claimed", description=f"You have claimed your daily reward of <:coin:1429548357206151401>{fmt(daily_reward)}!\nYour new balance is: <:coin:1429548357206151401>{fmt(new_balance)}", color=discord.Color.brand_green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    # If no user found, create new user with balance equal to daily reward and set last_daily
    insert_response = supabase_client.table("users").insert({"id": user_id, "balance": daily_reward, "last_daily": now.isoformat()}).execute()
    if insert_response.data:
        embed = discord.Embed(title="✅ Daily Reward Claimed", description=f"You have claimed your daily reward of <:coin:1429548357206151401>{fmt(daily_reward)}!\nYour new balance is: <:coin:1429548357206151401>{fmt(new_balance)}", color=discord.Color.brand_green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    await interaction.response.send_message("Error fetching or creating your balance. Please contact an admin.")

@bot.tree.command(name="weekly", description="Claim your weekly reward")
async def weekly_command(interaction: discord.Interaction):
    import datetime
    user_id = interaction.user.id
    # Fetch user balance and last_weekly from Supabase
    response = supabase_client.table("users").select("balance", "last_weekly").eq("id", user_id).execute()
    now = datetime.datetime.utcnow()
    weekly_reward = 5000
    if response.data and len(response.data) > 0:
        user = response.data[0]
        balance = user["balance"]
        last_weekly = user.get("last_weekly")
        if last_weekly:
            # Parse last_weekly as datetime
            try:
                last_weekly_dt = datetime.datetime.fromisoformat(last_weekly.replace("Z", "+00:00"))
            except Exception:
                last_weekly_dt = None
            if last_weekly_dt and (now - last_weekly_dt).total_seconds() < 604800:
                remaining = 604800 - (now - last_weekly_dt).total_seconds()
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600)
                minutes = int((remaining % 3600) // 60)
                embed = discord.Embed(title="⏳ Weekly Reward", description=f"You can claim your next weekly reward in ⌚{days}d {hours}h {minutes}m.", color=discord.Color.brand_red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        new_balance = balance + weekly_reward
        supabase_client.table("users").update({"balance": new_balance, "last_weekly": now.isoformat()}).eq("id", user_id).execute()
        embed = discord.Embed(title="✅ Weekly Reward Claimed", description=f"You have claimed your weekly reward of <:coin:1429548357206151401>{fmt(weekly_reward)}!\nYour new balance is: <:coin:1429548357206151401>{fmt(new_balance)}", color=discord.Color.brand_green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    # If no user found, create new user with balance equal to weekly reward and set last_weekly
    insert_response = supabase_client.table("users").insert({"id": user_id, "balance": weekly_reward, "last_weekly": now.isoformat()}).execute()
    if insert_response.data:
        embed = discord.Embed(title="✅ Weekly Reward Claimed", description=f"You have claimed your weekly reward of <:coin:1429548357206151401>{fmt(weekly_reward)}!\nYour new balance is: <:coin:1429548357206151401>{fmt(new_balance)}", color=discord.Color.brand_green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

class BlackjackView(discord.ui.View):
    def __init__(self, player_hand, dealer_hand, deck, bet, user_id, high_stakes=False):
        super().__init__(timeout=60)
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.bet = bet
        self.user_id = user_id
        self.finished = False
        self.high_stakes = high_stakes

    def hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            if card[:-1] in ['J', 'Q', 'K']:
                value += 10
            elif card[:-1] == 'A':
                aces += 1
                value += 11
            else:
                value += int(card[:-1])
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def hand_str(self, hand):
        return ', '.join(hand)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def update_embed(self, interaction, end=False):
        player_val = self.hand_value(self.player_hand)
        dealer_val = self.hand_value(self.dealer_hand)
        if self.high_stakes == True:
            embed = discord.Embed(title="<:cards:1429553211974619307> High Stakes Blackjack", color=discord.Color.from_str("#00A8B5"))
        else:
            embed = discord.Embed(title="<:cards:1429553211974619307> Blackjack", color=discord.Color.from_str("#00A8B5"))
        embed.add_field(name="Stake", value=f"Bet: <:coin:1429548357206151401>{fmt(self.bet)}", inline=False)
        embed.add_field(name="Your Hand", value=f"{self.hand_str(self.player_hand)}\nValue: {player_val}", inline=False)
        if end:
            embed.add_field(name="Dealer's Hand", value=f"{self.hand_str(self.dealer_hand)}\nValue: {dealer_val}", inline=False)
        else:
            embed.add_field(name="Dealer's Hand", value=f"{self.dealer_hand[0]}, ?", inline=False)
        if end:
            result = self.get_result()
            embed.add_field(name="Result", value=result, inline=False)
        await interaction.response.edit_message(embed=embed, view=None if end else self)

    def get_result(self):
        player_val = self.hand_value(self.player_hand)
        dealer_val = self.hand_value(self.dealer_hand)
        if player_val > 21:
            return "You busted! Dealer wins."
        elif dealer_val > 21:
            return "Dealer busted! You win!"
        elif player_val == dealer_val:
            return "Push! It's a tie."
        elif player_val > dealer_val:
            return "You win!"
        else:
            return "Dealer wins."

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(self.deck.pop())
        if self.hand_value(self.player_hand) > 21:
            self.finished = True
            await self.update_embed(interaction, end=True)
            await self.handle_payout(interaction)
        else:
            await self.update_embed(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Dealer's turn
        while self.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        self.finished = True
        await self.update_embed(interaction, end=True)
        await self.handle_payout(interaction)

    async def handle_payout(self, interaction):
        player_val = self.hand_value(self.player_hand)
        dealer_val = self.hand_value(self.dealer_hand)
        # Fetch user
        response = supabase_client.table("users").select("balance").eq("id", self.user_id).execute()
        balance = response.data[0]["balance"] if response.data and len(response.data) > 0 else 0
        payout = 0
        win_multiplier = 3 if self.high_stakes else 2
        if player_val > 21:
            payout = 0
        elif dealer_val > 21 or player_val > dealer_val:
            payout = self.bet * win_multiplier
        elif player_val == dealer_val:
            payout = self.bet
        else:
            payout = 0
        new_balance = balance - self.bet + payout
        supabase_client.table("users").update({"balance": new_balance}).eq("id", self.user_id).execute()
        result_str = (
            'won' if payout == self.bet * win_multiplier else
            'tied' if payout == self.bet else
            'lost'
        )
        embed = discord.Embed(title="💰 Game Over", color=discord.Color.from_str("#00A8B5"))
        embed.add_field(name="Result", value=f"You {result_str} <:coin:1429548357206151401>{fmt(self.bet)}.\nNew balance: <:coin:1429548357206151401>{fmt(new_balance)}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

def create_deck():
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

@bot.tree.command(name="blackjack", description="Play a game of blackjack.")
async def play_command(interaction: discord.Interaction, bet: int):
    user_id = interaction.user.id
    # Fetch user balance
    response = supabase_client.table("users").select("balance").eq("id", user_id).execute()
    balance = response.data[0]["balance"] if response.data and len(response.data) > 0 else 0
    if bet <= 0:
        await interaction.response.send_message("Bet must be greater than <:coin:1429548357206151401>0.", ephemeral=True)
        return
    if balance < bet:
        await interaction.response.send_message("Insufficient balance.", ephemeral=True)
        return
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    view = BlackjackView(player_hand, dealer_hand, deck, bet, user_id, high_stakes=False)
    embed = discord.Embed(title="<:cards:1429553211974619307> Blackjack", color=discord.Color.from_str("#00A8B5"))
    embed.add_field(name="Stake", value=f"Bet: <:coin:1429548357206151401>{fmt(bet)}", inline=False)
    embed.add_field(name="Your Hand", value=f"{view.hand_str(player_hand)}\nValue: {view.hand_value(player_hand)}", inline=False)
    embed.add_field(name="Dealer's Hand", value=f"{dealer_hand[0]}, ?", inline=False)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="highstakes", description="Play a high stakes game of blackjack.")
async def highstakes_command(interaction: discord.Interaction, bet: int):
    user_id = interaction.user.id
    # Fetch user balance
    response = supabase_client.table("users").select("balance").eq("id", user_id).execute()
    balance = response.data[0]["balance"] if response.data and len(response.data) > 0 else 0
    if bet <= 5000:
        await interaction.response.send_message("Bet must be greater than <:coin:1429548357206151401>5000.", ephemeral=True)
        return
    if balance < bet:
        await interaction.response.send_message("Insufficient balance.", ephemeral=True)
        return
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    view = BlackjackView(player_hand, dealer_hand, deck, bet, user_id, high_stakes=True)
    embed = discord.Embed(title="<:cards:1429553211974619307> High Stakes Blackjack", color=discord.Color.from_str("#00A8B5"))
    embed.add_field(name="Stake", value=f"Bet: <:coin:1429548357206151401>{fmt(bet)}", inline=False)
    embed.add_field(name="Your Hand", value=f"{view.hand_str(player_hand)}\nValue: {view.hand_value(player_hand)}", inline=False)
    embed.add_field(name="Dealer's Hand", value=f"{dealer_hand[0]}, ?", inline=False)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="coinflip", description="Flip a coin to win or lose money.")
async def coinflip_command(interaction: discord.Interaction, choice: str, amount: int):
    user_id = interaction.user.id
    choice = choice.lower()
    if choice not in ['heads', 'tails']:
        await interaction.response.send_message("Choice must be 'heads' or 'tails'.", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("Amount must be greater than <:coin:1429548357206151401>0.", ephemeral=True)
        return
    # Fetch user balance
    response = supabase_client.table("users").select("balance").eq("id", user_id).execute()
    balance = response.data[0]["balance"] if response.data and len(response.data) > 0 else 0
    if balance < amount:
        await interaction.response.send_message("Insufficient balance.", ephemeral=True)
        return
    result = random.choice(['heads', 'tails'])
    if result == choice:
        new_balance = balance + amount
        supabase_client.table("users").update({"balance": new_balance}).eq("id", user_id).execute()
        embed = discord.Embed(title="🪙 Coin Flip", description=f"You won! It was **{result}**.\nYou gained <:coin:1429548357206151401>{fmt(amount)}.\nNew balance: <:coin:1429548357206151401>{fmt(new_balance)}", color=discord.Color.brand_green())
    else:
        new_balance = balance - amount
        supabase_client.table("users").update({"balance": new_balance}).eq("id", user_id).execute()
        embed = discord.Embed(title="🪙 Coin Flip", description=f"You lost! It was **{result}**.\nYou lost <:coin:1429548357206151401>{fmt(amount)}.\nNew balance: <:coin:1429548357206151401>{fmt(new_balance)}", color=discord.Color.brand_red())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="diceroll", description="Roll a dice to win or lose money.")
async def diceroll_command(interaction: discord.Interaction, bet: int):
    user_id = interaction.user.id
    if bet <= 0:
        await interaction.response.send_message("Bet must be greater than <:coin:1429548357206151401>0.", ephemeral=True)
        return
    # Fetch user balance
    response = supabase_client.table("users").select("balance").eq("id", user_id).execute()
    balance = response.data[0]["balance"] if response.data and len(response.data) > 0 else 0
    if balance < bet:
        await interaction.response.send_message("Insufficient balance.", ephemeral=True)
        return
    # Choose two adjacent numbers from 1-6
    first = random.randint(1, 5)
    second = first + 1
    chosen = [first, second]

    class DiceRollView(discord.ui.View):
        def __init__(self, user_id, bet, chosen):
            super().__init__(timeout=30)
            self.user_id = user_id
            self.bet = bet
            self.chosen = chosen
            self.rolled = None

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.user_id

        @discord.ui.button(label="Roll Dice", style=discord.ButtonStyle.primary)
        async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.rolled = random.randint(1, 6)
            # Fetch user balance again
            response = supabase_client.table("users").select("balance").eq("id", self.user_id).execute()
            balance = response.data[0]["balance"] if response.data and len(response.data) > 0 else 0
            if self.rolled in self.chosen:
                new_balance = balance + self.bet * 2
                supabase_client.table("users").update({"balance": new_balance}).eq("id", self.user_id).execute()
                result = f"🎲 You rolled **{self.rolled}**! You win <:coin:1429548357206151401>{fmt(self.bet * 2)}.\nNew balance: <:coin:1429548357206151401>{fmt(new_balance)}"
                color = discord.Color.brand_green()
            else:
                new_balance = balance - self.bet
                supabase_client.table("users").update({"balance": new_balance}).eq("id", self.user_id).execute()
                result = f"🎲 You rolled **{self.rolled}**! You lost <:coin:1429548357206151401>{fmt(self.bet)}.\nNew balance: <:coin:1429548357206151401>{fmt(new_balance)}"
                color = discord.Color.brand_red()
            embed = discord.Embed(title="🎲 Dice Roll", description=result, color=color)
            await interaction.response.edit_message(embed=embed, view=None)

    view = DiceRollView(user_id, bet, chosen)
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"Pick: **{chosen[0]}** or **{chosen[1]}**\nIf you roll either, you win <:coin:1429548357206151401>{fmt(bet * 2)}! Otherwise, you lose <:coin:1429548357206151401>{fmt(bet)}.",
        color=discord.Color.from_str("#00A8B5")
    )
    await interaction.response.send_message(embed=embed, view=view)
    

class LeaderboardSelect(discord.ui.Select):
    def __init__(self, interaction):
        options = [
            discord.SelectOption(label="Global", value="global", description="Show the top 10 players globally."),
            discord.SelectOption(label="Server", value="server", description="Show the top 10 players in this server."),
        ]
        super().__init__(placeholder="Choose leaderboard type...", min_values=1, max_values=1, options=options)
        self.interaction = interaction

    async def callback(self, select_interaction: discord.Interaction):
        leaderboard_type = self.values[0]
        if leaderboard_type == "global":
            # Fetch top 10 globally
            response = supabase_client.table("users").select("id", "balance").order("balance", desc=True).limit(10).execute()
            entries = response.data if response.data else []
            title = "Global Leaderboard"
        else:
            # Fetch top 10 in this server (by user IDs in this guild)
            guild = self.interaction.guild
            if not guild:
                await select_interaction.response.send_message("This command must be used in a server for server leaderboard.", ephemeral=True)
                return
            member_ids = [member.id for member in guild.members if not member.bot]
            if not member_ids:
                await select_interaction.response.send_message("No members found in this server.", ephemeral=True)
                return
            response = supabase_client.table("users").select("id", "balance").in_("id", member_ids).order("balance", desc=True).limit(10).execute()
            entries = response.data if response.data else []
            title = f"Leaderboard for {guild.name}"
        desc = ""
        for i, entry in enumerate(entries, 1):
            user_id = entry["id"]
            balance = entry["balance"]
            user = self.interaction.client.get_user(user_id)
            name = user.display_name if user else f"<@{user_id}>"
            desc += f"**{i}.** {name} — <:coin:1429548357206151401>{fmt(balance)}\n"
        if not desc:
            desc = "No data found."
        embed = discord.Embed(title=title, description=desc, color=discord.Color.from_str("#00A8B5"))
        await select_interaction.response.edit_message(embed=embed, view=self.view)

@bot.tree.command(name="leaderboard", description="View the leaderboard")
async def leaderboard_command(interaction: discord.Interaction):
    view = discord.ui.View()
    select = LeaderboardSelect(interaction)
    view.add_item(select)
    embed = discord.Embed(title="Leaderboard", description="Select a leaderboard type from the dropdown below.", color=discord.Color.from_str("#00A8B5"))
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        description="# Blackjack Help\n> Thank you for using Blackjack. Below is a list of available commands for you to use. If you require further assistance, please visit our [Support Server](https://discord.gg/DPzkYc7pZr).\n## Commands",
        color=discord.Color.from_str("#00A8B5")
    )
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description or "No description", inline=True)
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)