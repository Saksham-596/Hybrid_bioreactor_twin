import numpy as np
import pandas as pd
from scipy.integrate import odeint

 
def reality_kinetics(y, t, mu_max, Ks, Y, D, Sf, Ki, toxicity):
    X, S = y
    actual_mu_max = mu_max * (1.0 - toxicity)
    mu_real = (actual_mu_max * S) / (Ks + S + (S**2 / Ki)) 
    
    dXdt = (mu_real - D) * X
    dSdt = D * (Sf - S) - (mu_real * X) / Y
    return [dXdt, dSdt]

def ideal_kinetics(y, t, mu_max, Ks, Y, D, Sf):
    X, S = y
    mu = (mu_max * S) / (Ks + S)
    dXdt = (mu - D) * X
    dSdt = D * (Sf - S) - (mu * X) / Y
    return [dXdt, dSdt]

def generate_training_data(num_batches=100):
    t = np.linspace(0, 50, 100) 
    dataset = []

    print(f"Generating {num_batches} simulated batches...")

    for batch_id in range(num_batches):
       
        X0 = np.random.uniform(0.05, 0.15)
        S0 = np.random.uniform(15.0, 25.0)
        y0 = [X0, S0]
        
        # Standard parameters
        mu_max, Ks, Y, D, Sf = 0.5, 2.0, 0.5, 0.1, 20.0
        
        Ki = np.random.uniform(10.0, 50.0) #Inhibition constant
        toxicity = np.random.uniform(0.0, 0.3) # 0% to 30% loss of efficiency

       
        ideal_sol = odeint(ideal_kinetics, y0, t, args=(mu_max, Ks, Y, D, Sf))
        real_sol = odeint(reality_kinetics, y0, t, args=(mu_max, Ks, Y, D, Sf, Ki, toxicity))

        real_X = real_sol[:, 0] + np.random.normal(0, 0.02, len(t))
        real_S = real_sol[:, 1] + np.random.normal(0, 0.5, len(t))
        ideal_X = ideal_sol[:, 0]
        ideal_S = ideal_sol[:, 1]

        error_X = real_X - ideal_X

        for i in range(len(t)):
            dataset.append({
                "batch_id": batch_id,
                "time": round(t[i], 2),
                "ideal_X": round(ideal_X[i], 4),
                "ideal_S": round(ideal_S[i], 4),
                "real_X": round(real_X[i], 4),
                "real_S": round(real_S[i], 4),
                "error_X": round(error_X[i], 4), 
                "toxicity_factor": round(toxicity, 4) 
            })
    df = pd.DataFrame(dataset)
    df.to_csv("bioreactor_training_data.csv", index=False)
    print("Saved to bioreactor_training_data.csv. Ready for ML training.")
    
if __name__ == "__main__":
    generate_training_data(100)