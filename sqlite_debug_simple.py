import sqlite3
import os

db_path = os.path.join("instance", "clp_calculator.db")

def get_mixture_details(mixture_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, final_health_hazards FROM mixture WHERE id=?", (mixture_id,))
    mixture = cursor.fetchone()
    if not mixture:
        print(f"Směs {mixture_id} nenalezena.")
        return
    
    print(f"MIX: {mixture['name']}")
    print(f"HAZARDS: {mixture['final_health_hazards']}")
    
    cursor.execute("""
        SELECT mc.concentration, s.name, s.health_h_phrases, s.scl_limits 
        FROM mixture_component mc
        JOIN substance s ON mc.substance_id = s.id
        WHERE mc.mixture_id = ?
    """, (mixture_id,))
    
    for c in cursor.fetchall():
        print(f"COMPONENT: {c['name']}")
        print(f"  CONC: {c['concentration']}")
        print(f"  H: {c['health_h_phrases']}")
        print(f"  SCL: {c['scl_limits']}")
    
    conn.close()

if __name__ == "__main__":
    get_mixture_details(5)
