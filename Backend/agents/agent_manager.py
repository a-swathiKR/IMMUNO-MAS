from agents.portfolio_manager import PortfolioManager


class AgentManager:

    def __init__(self):
        self.portfolio_manager = PortfolioManager()

    def run_system(self):
        return self.portfolio_manager.make_decision()

    def collect_baseline(self, iterations=20):

        results = []

        for i in range(iterations):

            result = self.run_system()

            results.append({
                "iteration": i + 1,
                "decision": result["decision"]
            })

        return {
            "total_executions": iterations,
            "results": results
        }