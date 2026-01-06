from db.models import create_tables
from db.preset_words import add_initial_presets
from core.config import engine
from bot.handlers import *


if "__main__" == __name__:
    print("Bot working...")
    create_tables(engine)
    add_initial_presets(engine)
    bot.polling(non_stop=True, skip_pending=True)
