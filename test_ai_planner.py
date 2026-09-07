from ai.factory import AIProviderFactory
from ai.planner import AIPlanner
from config.settings import get_settings


def main() -> None:
    # -----------------------------------------------------
    # SETTINGS
    # -----------------------------------------------------

    settings = get_settings()

    print("AI Provider:", settings.ai_provider)
    print("AI Model:", settings.ai_model)
    print("Ollama URL:", settings.ollama_base_url)

    # -----------------------------------------------------
    # AI PROVIDER
    # -----------------------------------------------------

    provider_result = AIProviderFactory.create(
        settings
    )

    if provider_result.is_failure():
        print()
        print("PROVIDER ERROR")
        print("================")
        print(provider_result.error)
        return

    provider = provider_result.require_data()

    print()
    print("AI PROVIDER READY")
    print("=================")

    # -----------------------------------------------------
    # AI PLANNER
    # -----------------------------------------------------

    planner = AIPlanner(
        provider
    )

    result = planner.create_plan(
        "Create a Python calculator application."
    )

    if result.is_failure():
        print()
        print("PLANNER ERROR")
        print("================")
        print(result.error)
        return

    # -----------------------------------------------------
    # DISPLAY PLAN
    # -----------------------------------------------------

    steps = result.require_data()

    print()
    print("AI GENERATED PLAN")
    print("=================")

    for index, step in enumerate(
        steps,
        start=1,
    ):
        print()
        print(f"STEP {index}")
        print(f"Name: {step['name']}")
        print(
            f"Description: {step['description']}"
        )
        print(f"Action: {step['action']}")
        print(
            f"Approval: "
            f"{step['requires_approval']}"
        )
        print(
            f"Metadata: "
            f"{step['metadata']}"
        )


if __name__ == "__main__":
    main()