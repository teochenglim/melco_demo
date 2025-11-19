"""
Configuration for Casino Gaming Transaction Generator
"""

# Kafka/Redpanda Configuration
KAFKA_BOOTSTRAP_SERVERS = ['redpanda:9092']  # Redpanda internal port (use localhost:19092 for external)
KAFKA_TOPIC = 'gaming-transactions'
EVENTS_PER_SECOND = 5

# Member pool (simulated casino members - 100 members)
# IDs 1001-1020: High rollers (big bets, guaranteed wins - will hit hotel threshold)
# IDs 1021-1050: Regular players (medium bets, normal luck)
# IDs 1051-1070: Unlucky players (will lose consistently - hit drink threshold)
# IDs 1071-1100: Casual players (small bets, mixed results)

# Generate 100 members
FIRST_NAMES = ["John", "Emily", "Michael", "Sarah", "David", "Lisa", "Robert", "Jennifer", "James", "Matthew",
               "Amanda", "Christopher", "Michelle", "Daniel", "Jessica", "William", "Ashley", "Richard", "Stephanie", "Joseph",
               "Nicole", "Thomas", "Elizabeth", "Charles", "Rebecca", "Brian", "Laura", "Kevin", "Kimberly", "Steven",
               "Donna", "Mark", "Carol", "Donald", "Sandra", "George", "Nancy", "Kenneth", "Betty", "Edward",
               "Margaret", "Ronald", "Sharon", "Timothy", "Cynthia", "Jason", "Kathleen", "Jeffrey", "Amy", "Ryan",
               "Angela", "Jacob", "Melissa", "Gary", "Brenda", "Nicholas", "Emma", "Eric", "Anna", "Stephen",
               "Samantha", "Jonathan", "Rebecca", "Larry", "Katherine", "Justin", "Christine", "Scott", "Debra", "Brandon",
               "Rachel", "Benjamin", "Catherine", "Samuel", "Carolyn", "Frank", "Janet", "Gregory", "Maria", "Raymond",
               "Heather", "Alexander", "Diane", "Patrick", "Ruth", "Jack", "Julie", "Dennis", "Olivia", "Jerry",
               "Sophia", "Tyler", "Victoria", "Aaron", "Madison", "Jose", "Grace", "Adam", "Hannah", "Henry"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
              "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
              "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez",
              "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart",
              "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
              "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
              "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes", "Price",
              "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez", "Powell"]

MEMBERS = [(1000 + i + 1, f"{FIRST_NAMES[i]} {LAST_NAMES[i]}") for i in range(100)]

# Unlucky members who lose more often (for drink offers) - IDs 1051-1070
UNLUCKY_MEMBERS = set(range(1051, 1071))

# Game types and their house edges / bet ranges
GAMES = {
    'slot': {
        'house_edge': 0.08,  # 8% house edge
        'min_bet': 10,
        'max_bet': 500,
        'win_multiplier': (0, 20),  # Can win 0x to 20x
        'popularity': 0.4  # 40% of all bets
    },
    'blackjack': {
        'house_edge': 0.02,  # 2% house edge (skilled players)
        'min_bet': 25,
        'max_bet': 1000,
        'win_multiplier': (0.95, 1.5),  # Typically win ~1x or lose
        'popularity': 0.25
    },
    'roulette': {
        'house_edge': 0.053,  # 5.3% house edge
        'min_bet': 10,
        'max_bet': 500,
        'win_multiplier': (0, 35),  # Can win up to 35x on single number
        'popularity': 0.20
    },
    'poker': {
        'house_edge': 0.05,  # 5% rake
        'min_bet': 50,
        'max_bet': 2000,
        'win_multiplier': (0, 5),
        'popularity': 0.15
    }
}

# Win probabilities for each game type
# Adjusted to create realistic house edge
WIN_PROBABILITIES = {
    'slot': 0.45,      # Win 45% of time, but payouts average to 92% RTP
    'blackjack': 0.48, # Win 48% of time (2% house edge)
    'roulette': 0.47,  # Win 47% of time (5.3% house edge with payouts)
    'poker': 0.46      # Win 46% of time (5% house edge)
}

# Unlucky members win only 35% as often
UNLUCKY_WIN_MULTIPLIER = 0.35
