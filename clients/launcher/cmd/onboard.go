package cmd

import (
	"fmt"
	"strings"

	"charm.land/huh/v2"
	"github.com/PurpleAILAB/Decepticon/clients/launcher/internal/config"
	"github.com/PurpleAILAB/Decepticon/clients/launcher/internal/ui"
	"github.com/spf13/cobra"
)

var resetFlag bool

var onboardCmd = &cobra.Command{
	Use:   "onboard",
	Short: "Configure Decepticon (authentication, provider strategy, model profile)",
	RunE:  runOnboard,
}

func init() {
	onboardCmd.Flags().BoolVar(&resetFlag, "reset", false, "Reconfigure even if .env already exists")
	rootCmd.AddCommand(onboardCmd)
}

func runOnboard(cmd *cobra.Command, args []string) error {
	if config.EnvExists() && !resetFlag {
		ui.Info(".env already configured at " + config.EnvPath())
		ui.DimText("Run 'decepticon onboard --reset' to reconfigure")
		return nil
	}

	var (
		authMethod       string
		providerStrategy string
		llmProvider      string
		apiKey           string
		openrouterKey    string
		profile          string
		useLangSmith     bool
		langSmithKey     string
	)

	form := huh.NewForm(
		// Intro
		huh.NewGroup(
			huh.NewNote().
				Title("Decepticon Setup").
				Description("Configure authentication, provider strategy,\nmodel profile, and observability.\n\nUse ↑↓ to navigate, Enter to confirm."),
		),

		// Step 1: Authentication method
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("Authentication Method").
				Description("How should Decepticon authenticate with LLM providers?").
				Options(
					huh.NewOption("API Key — Direct API access via x-api-key header", "api"),
					huh.NewOption("OAuth  — Subscription-based (Claude Code, Codex)", "auth"),
				).
				Value(&authMethod),
		).Title("1 / 6  ·  Authentication").
			Description("Choose how to connect to LLM services"),

		// Step 2: Provider Strategy (NEW - only for API key mode)
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("Provider Strategy").
				Description("How should Decepticon route model requests?").
				Options(
					huh.NewOption("Direct APIs     — Individual provider keys (standard)", "direct"),
					huh.NewOption("OpenRouter      — Single key for 200+ models (cost-optimized)", "openrouter"),
					huh.NewOption("Hybrid          — Mix direct + OpenRouter (best of both)", "hybrid"),
				).
				Value(&providerStrategy),
			huh.NewNote().
				Title("Strategy Details:").
				Description(
					"• Direct APIs: Use ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.\n"+
						"  Best rate limits, standard approach.\n\n"+
						"• OpenRouter: Single OPENROUTER_API_KEY for all models.\n"+
						"  Access 200+ models, 10-30% cheaper, unified billing.\n\n"+
						"• Hybrid: Direct Anthropic + OpenRouter for others.\n"+
						"  Optimal cost/performance balance.",
				),
		).Title("2 / 6  ·  Provider Strategy").
			Description("Choose your model routing approach").
			WithHideFunc(func() bool {
				return authMethod == "auth"
			}),

		// Step 3: Provider selection (only for direct/hybrid strategies)
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("LLM Provider").
				Description("Which provider will power the agents?").
				OptionsFunc(func() []huh.Option[string] {
					if authMethod == "auth" {
						return []huh.Option[string]{
							huh.NewOption("Claude Code  — Anthropic OAuth", "claude-code"),
							huh.NewOption("Codex        — coming soon", "codex"),
						}
					}
					return []huh.Option[string]{
						huh.NewOption("Anthropic  — Claude Opus / Sonnet / Haiku", "anthropic"),
						huh.NewOption("OpenAI     — GPT-5.4 / GPT-4.1", "openai"),
						huh.NewOption("Google     — Gemini 2.5 Flash", "google"),
						huh.NewOption("MiniMax    — M2.7", "minimax"),
					}
				}, &authMethod).
				Value(&llmProvider),
		).Title("3 / 6  ·  Provider").
			Description("Select your primary LLM provider").
			WithHideFunc(func() bool {
				return authMethod == "auth" || providerStrategy == "openrouter"
			}),

		// Step 4a: Direct provider API key (for direct/hybrid strategies)
		huh.NewGroup(
			huh.NewInput().
				TitleFunc(func() string {
					switch llmProvider {
					case "anthropic":
						return "Anthropic API Key"
					case "openai":
						return "OpenAI API Key"
					case "google":
						return "Google API Key"
					case "minimax":
						return "MiniMax API Key"
					}
					return "API Key"
				}, &llmProvider).
				PlaceholderFunc(func() string {
					switch llmProvider {
					case "anthropic":
						return "sk-ant-..."
					case "openai":
						return "sk-..."
					case "google":
						return "AIza..."
					case "minimax":
						return "eyJ..."
					}
					return ""
				}, &llmProvider).
				DescriptionFunc(func() string {
					if providerStrategy == "hybrid" {
						return "Direct API key for " + llmProvider + " (best rate limits)"
					}
					return "Enter your " + llmProvider + " API key"
				}, &providerStrategy).
				EchoMode(huh.EchoModePassword).
				Value(&apiKey).
				Validate(func(s string) error {
					if s == "" {
						return fmt.Errorf("API key is required")
					}
					return nil
				}),
		).Title("4 / 6  ·  Credentials").
			Description("Enter your provider API key").
			WithHideFunc(func() bool {
				return authMethod == "auth" || providerStrategy == "openrouter"
			}),

		// Step 4b: OpenRouter API key (for openrouter/hybrid strategies)
		huh.NewGroup(
			huh.NewInput().
				Title("OpenRouter API Key").
				Placeholder("sk-or-v1-...").
				DescriptionFunc(func() string {
					if providerStrategy == "hybrid" {
						return "OpenRouter key for non-Anthropic models (GPT, Gemini, Llama, etc.)"
					}
					return "Get your key at: https://openrouter.ai/keys"
				}, &providerStrategy).
				EchoMode(huh.EchoModePassword).
				Value(&openrouterKey).
				Validate(func(s string) error {
					if s == "" {
						return fmt.Errorf("OpenRouter API key is required")
					}
					if !strings.HasPrefix(s, "sk-or-") {
						return fmt.Errorf("OpenRouter keys start with 'sk-or-'")
					}
					return nil
				}),
			huh.NewNote().
				Title("OpenRouter Benefits:").
				Description(
					"• Access 200+ models from one API key\n"+
						"• Anthropic, OpenAI, Google, Meta, Mistral, Cohere, etc.\n"+
						"• 10-30% cheaper than direct APIs\n"+
						"• Unified billing across all providers",
				),
		).Title("4 / 6  ·  Credentials").
			Description("Enter your OpenRouter API key").
			WithHideFunc(func() bool {
				return authMethod == "auth" || (providerStrategy != "openrouter" && providerStrategy != "hybrid")
			}),

		// Step 5: Model profile
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("Model Profile").
				Description("Controls which models each agent tier uses").
				Options(
					huh.NewOption("eco  — Opus + Sonnet + Haiku mix (recommended)", "eco"),
					huh.NewOption("max  — Opus everywhere (expensive)", "max"),
					huh.NewOption("test — Haiku only (for development)", "test"),
				).
				Value(&profile),
		).Title("5 / 6  ·  Performance").
			Description("Balance between cost and capability"),

		// Step 6: LangSmith tracing
		huh.NewGroup(
			huh.NewConfirm().
				Title("Enable LangSmith?").
				Description("LLM observability and trace collection").
				Affirmative("Yes").
				Negative("No").
				Value(&useLangSmith),
		).Title("6 / 6  ·  Observability").
			Description("Optional tracing integration"),

		// LangSmith API key (only when enabled)
		huh.NewGroup(
			huh.NewInput().
				Title("LangSmith API Key").
				Placeholder("lsv2_...").
				EchoMode(huh.EchoModePassword).
				Value(&langSmithKey).
				Validate(func(s string) error {
					if s == "" {
						return fmt.Errorf("LangSmith API key is required")
					}
					return nil
				}),
		).Title("6 / 6  ·  Observability").
			Description("Enter your LangSmith credentials").
			WithHideFunc(func() bool {
				return !useLangSmith
			}),
	).WithTheme(huh.ThemeFunc(ui.DecepticonTheme))

	if err := form.Run(); err != nil {
		return fmt.Errorf("setup cancelled: %w", err)
	}

	// Build values map
	values := map[string]string{
		"DECEPTICON_MODEL_PROFILE": profile,
	}

	// Set DECEPTICON_MODEL_PROVIDER based on auth method and provider strategy
	if authMethod == "auth" {
		values["DECEPTICON_MODEL_PROVIDER"] = authMethod
	} else {
		// For API key mode, map provider strategy to the expected value
		switch providerStrategy {
		case "direct":
			values["DECEPTICON_MODEL_PROVIDER"] = "api"
		case "openrouter":
			values["DECEPTICON_MODEL_PROVIDER"] = "openrouter"
		case "hybrid":
			values["DECEPTICON_MODEL_PROVIDER"] = "hybrid"
		default:
			// Backward compatibility: default to "api" if strategy not set
			values["DECEPTICON_MODEL_PROVIDER"] = "api"
		}
	}

	// Add direct provider API keys (for direct and hybrid strategies)
	if authMethod == "api" && apiKey != "" && (providerStrategy == "direct" || providerStrategy == "hybrid") {
		switch llmProvider {
		case "anthropic":
			values["ANTHROPIC_API_KEY"] = apiKey
		case "openai":
			values["OPENAI_API_KEY"] = apiKey
		case "google":
			values["GOOGLE_API_KEY"] = apiKey
		case "minimax":
			values["MINIMAX_API_KEY"] = apiKey
		}
	}

	// Add OpenRouter API key (for openrouter and hybrid strategies)
	if authMethod == "api" && openrouterKey != "" && (providerStrategy == "openrouter" || providerStrategy == "hybrid") {
		values["OPENROUTER_API_KEY"] = openrouterKey
	}

	// Add LangSmith configuration
	if useLangSmith && langSmithKey != "" {
		values["LANGSMITH_TRACING"] = "true"
		values["LANGSMITH_API_KEY"] = langSmithKey
		values["LANGSMITH_PROJECT"] = "decepticon"
	}

	if err := config.WriteEnvFromEmbed(config.EnvPath(), values); err != nil {
		return fmt.Errorf("write .env: %w", err)
	}

	// Summary
	fmt.Println()
	fmt.Println(ui.Green.Render("  ✓ Configuration saved"))
	fmt.Println()
	fmt.Println(ui.Dim.Render("  ┌──────────────────────────────────────┐"))
	fmt.Println(ui.Dim.Render("  │") + ui.Cyan.Render("  Auth      ") + ui.Dim.Render(authMethod))

	// Show provider strategy for API key mode
	if authMethod == "api" {
		strategyDisplay := providerStrategy
		if providerStrategy == "direct" {
			strategyDisplay = "direct (" + llmProvider + ")"
		}
		fmt.Println(ui.Dim.Render("  │") + ui.Cyan.Render("  Strategy  ") + ui.Dim.Render(strategyDisplay))
	} else {
		fmt.Println(ui.Dim.Render("  │") + ui.Cyan.Render("  Provider  ") + ui.Dim.Render(llmProvider))
	}

	fmt.Println(ui.Dim.Render("  │") + ui.Cyan.Render("  Profile   ") + ui.Dim.Render(profile))

	if useLangSmith {
		fmt.Println(ui.Dim.Render("  │") + ui.Cyan.Render("  LangSmith ") + ui.Green.Render("enabled"))
	}

	fmt.Println(ui.Dim.Render("  │"))
	fmt.Println(ui.Dim.Render("  │  ") + ui.Dim.Render(config.EnvPath()))
	fmt.Println(ui.Dim.Render("  └──────────────────────────────────────┘"))
	fmt.Println()

	// Show helpful next steps based on provider strategy
	if authMethod == "api" && providerStrategy == "openrouter" {
		ui.DimText("  OpenRouter provides access to 200+ models")
		ui.DimText("  View available models: https://openrouter.ai/models")
		fmt.Println()
	} else if authMethod == "api" && providerStrategy == "hybrid" {
		ui.DimText("  Hybrid mode: Direct " + llmProvider + " + OpenRouter for others")
		ui.DimText("  Optimal cost/performance balance")
		fmt.Println()
	}

	ui.DimText("  Run 'decepticon' to start the platform")
	return nil
}
