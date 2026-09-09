import math

# ---------- Functions ----------

def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    if height_m <= 0:
        raise ValueError("Height must be greater than zero.")
    bmi = weight / (height_m ** 2)
    return round(bmi, 2)


def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal Weight"
    elif bmi < 30:
        return "Overweight"
    elif bmi < 35:
        return "Obesity (Class 1)"
    elif bmi < 40:
        return "Obesity (Class 2)"
    else:
        return "Extreme Obesity (Class 3)"


def ideal_weight_range(height_cm):
    height_m = height_cm / 100
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)
    return round(min_weight, 1), round(max_weight, 1)


def health_tips(category):
    tips = {
        "Underweight": [
            "Eat more protein-rich foods",
            "Increase healthy calorie intake",
            "Do strength training"
        ],
        "Normal Weight": [
            "Maintain balanced diet",
            "Exercise regularly",
            "Stay hydrated"
        ],
        "Overweight": [
            "Reduce sugary foods",
            "Increase daily exercise",
            "Track calorie intake"
        ],
        "Obesity (Class 1)": [
            "Follow a healthy diet plan",
            "Exercise daily",
            "Consult a healthcare professional"
        ],
        "Obesity (Class 2)": [
            "Seek medical guidance",
            "Focus on long-term weight management",
            "Avoid processed foods"
        ],
        "Extreme Obesity (Class 3)": [
            "Immediate medical consultation recommended",
            "Adopt supervised fitness plans",
            "Monitor health regularly"
        ]
    }
    return tips.get(category, [])


def bmi_meter(bmi):
    meter = int(min(max(bmi, 0), 40))
    meter_line = "".join("🔴" if i == meter else "─" for i in range(41))
    return f"BMI VISUAL METER\n{'-' * 50}\n{meter_line}\n0    18.5    25    30    35    40+"


def run():
    import streamlit as st

    st.title("📏 BMI Calculator")
    weight = st.number_input("Weight (kg)", min_value=1.0, value=70.0)
    height = st.number_input("Height (cm)", min_value=1.0, value=170.0)

    if st.button("Calculate BMI"):
        bmi = calculate_bmi(weight, height)
        category = bmi_category(bmi)
        min_weight, max_weight = ideal_weight_range(height)

        st.metric("BMI", f"{bmi:.2f}")
        st.write(f"**Category:** {category}")
        st.write(f"**Ideal Weight Range:** {min_weight} kg - {max_weight} kg")

        st.write("**Health Tips:**")
        for tip in health_tips(category):
            st.write(f"- {tip}")

        st.text(bmi_meter(bmi))


# ---------- Main Program ----------

def main():
    print("=" * 45)
    print("        ADVANCED BMI CALCULATOR")
    print("=" * 45)

    name = input("Enter your name: ")
    age = int(input("Enter your age: "))
    gender = input("Enter your gender (Male/Female): ")

    weight = float(input("Enter your weight (kg): "))
    height = float(input("Enter your height (cm): "))

    if height <= 0:
        print("Height must be greater than zero.")
        return

    bmi = calculate_bmi(weight, height)
    category = bmi_category(bmi)
    min_weight, max_weight = ideal_weight_range(height)

    print("\n" + "=" * 45)
    print("              BMI REPORT")
    print("=" * 45)
    print(f"Name            : {name}")
    print(f"Age             : {age}")
    print(f"Gender          : {gender}")
    print(f"Weight          : {weight} kg")
    print(f"Height          : {height} cm")
    print(f"BMI             : {bmi}")
    print(f"Category        : {category}")
    print(f"\nIdeal Weight Range: {min_weight} kg - {max_weight} kg")

    print("\nHealth Tips:")
    for tip in health_tips(category):
        print(f"✔ {tip}")

    print(bmi_meter(bmi))
    print("\nThank you for using the BMI Calculator!")


if __name__ == "__main__":
    main()