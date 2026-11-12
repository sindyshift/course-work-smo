from simulation import SimulationModel

if __name__ == "__main__":
  sim = SimulationModel(ns=3, bc=3, nd=2, a=0.5, b=1.5, mu=0.8)

  print("Выберите режим работы:")
  print("1 - Автоматический режим с итерационным расчетом N (ОР1)")
  print("2 - Пошаговый режим (ОД2)")

  mode = input("Введите номер режима (1 или 2): ").strip()

  if mode == "1":
    sim.run_automatic_mode()
  elif mode == "2":
    print("\n--- ПОШАГОВЫЙ РЕЖИМ (ОД2) ---")
    print("Нажимайте Enter для перехода к следующему шагу модели.\n")
    input("Нажмите Enter для старта...")
    step_n = 1
    while True:

      cmd = input(f"[Шаг {step_n}] Нажмите Enter (или q для выхода): ")
      if cmd.strip().lower() == "q":
        print("Выход из пошагового режима.")
        break
      sim.step(step_n)
      step_n += 1
  else:
    print("Неверный ввод. Пожалуйста, выберите 1 или 2.")