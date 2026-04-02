/**
 * Commitlint configuration
 * Enforces conventional commits format
 *
 * Format: <type>(<scope>): <subject>
 * Example: feat(portfolio): add stock filtering feature
 */

export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "feat", // New feature
        "fix", // Bug fix
        "docs", // Documentation changes
        "style", // Code style changes (formatting, etc.)
        "refactor", // Code refactoring
        "perf", // Performance improvements
        "test", // Adding or updating tests
        "build", // Build system changes
        "ci", // CI/CD changes
        "chore", // Other changes that don't modify src or test files
        "revert", // Revert previous commit
      ],
    ],
    "subject-case": [2, "never", ["upper-case", "pascal-case"]],
    "subject-empty": [2, "never"],
    "subject-full-stop": [2, "never", "."],
    "header-max-length": [2, "always", 100],
    "body-leading-blank": [2, "always"],
    "footer-leading-blank": [2, "always"],
  },
};
