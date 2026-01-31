import sqlite3
import os

db_path = os.path.join("instance", "clp_calculator.db")

def get_mixture_details(mixture_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Směs
    cursor.execute("SELECT * FROM mixture WHERE id=?", (mixture_id,))
    mixture = cursor.fetchone()
    if not mixture:
        print(f"Směs {mixture_id} nenalezena.")
        return
    
    print(f"SMĚS: {mixture['name']} (ID: {mixture['id']})")
    print(f"Aktuální klasifikace: {mixture['final_health_hazards']}")
    print("-" * 50)
    
    # 2. Komponenty
    cursor.execute("""
        SELECT mc.concentration, s.name, s.health_h_phrases, s.scl_limits 
        FROM mixture_component mc
        JOIN substance s ON mc.substance_id = s.id
        WHERE mc.mixture_id = ?
    """, (mixture_id,))
    
    components = cursor.fetchall()
    for c in components:
        print(f"Látka: {c['name']}")
        print(f"  Koncentrace: {c['concentration']}%")
        print(f"  H-věty: {c['health_h_phrases']}")
        print(f"  SCL: {c['scl_limits']}")
        print("-" * 30)
    
    conn.close()

if __name__ == "__main__":
    get_mixture_details(5)
