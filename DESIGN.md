# Tube reliability demo design

The landing page is the product: all eleven Tube lines moving through one rating history, with the current ranking immediately below.

The interface uses the live collector's bounded Elo-style ratings and preserves the original hackathon archive as a separate data source. Timeframe controls change the visible history without hiding lines, and each line can be focused from the legend. The table keeps official line colours, service state and the current score together.

The visual language is a compressed departure board: dark navy, narrow type, hard rules and restrained yellow for ratings. It stays numerical without looking like a generic analytics dashboard.

Rules:

- Always show all eleven lines on first load.
- Never present sampled predictions as confirmed movements or cancellations.
- Keep live and archived observations visibly separate.
- Ratings stay between 100 and 3,500 and retain restoring pressure toward 1,500.
- Desktop and mobile preserve timeframe controls, line focus, export and source switching.
