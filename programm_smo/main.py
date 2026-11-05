from simulation import SimulationModel

if __name__ == "__main__":

  sim = SimulationModel(
      ns=4, bc=2, nd=1, a=0.2, b=0.5, mu=0.2
  )

  print("--- ПОШАГОВЫЙ РЕЖИМ: ДЕМОНСТРАЦИЯ ПЕРЕПОЛНЕНИЯ БУФЕРА (ВАРИАНТ 8) ---")
  print("Как только буфер заполнится (2/2), вы увидите отказ и выбивание старой заявки (Д1ОО4).\n")
  input("Нажмите Enter для старта первого шага...")

  for step in range(1, 10):
    sim.step(step)
    input(f"[Шаг {step}] Нажмите Enter для перехода к следующему шагу...")