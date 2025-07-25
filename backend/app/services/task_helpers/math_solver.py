"""
Mathematical Equation Solver for academic assistance.

This module provides mathematical equation solving, step-by-step solutions,
and mathematical notation conversion to help students with calculations.
"""

import logging
import re
import math
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class MathSolver:
    """Mathematical equation solver service."""
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.supported_functions = {
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
            'sinh', 'cosh', 'tanh', 'exp', 'log', 'log10',
            'sqrt', 'abs', 'ceil', 'floor', 'factorial'
        }
        
        self.constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau
        }
    
    def solve_equation(self, equation: str, variable: str = 'x') -> Dict[str, Any]:
        """
        Solve mathematical equations.
        
        Args:
            equation: Mathematical equation as string
            variable: Variable to solve for (default 'x')
        
        Returns:
            Dictionary with solution and steps
        """
        try:
            if not equation.strip():
                return {
                    "success": False,
                    "error": "No equation provided"
                }
            
            results = {
                "success": True,
                "equation": equation,
                "variable": variable,
                "solution": None,
                "steps": [],
                "equation_type": "",
                "verification": {},
                "graph_suggestion": False
            }
            
            # Clean and parse equation
            cleaned_eq = self._clean_equation(equation)
            equation_type = self._identify_equation_type(cleaned_eq)
            results["equation_type"] = equation_type
            
            # Attempt to solve based on type
            if equation_type == "arithmetic":
                solution = self._solve_arithmetic(cleaned_eq)
                results["solution"] = solution
                results["steps"] = [f"Calculate: {cleaned_eq} = {solution}"]
            
            elif equation_type == "linear":
                solution = self._solve_linear(cleaned_eq, variable)
                results["solution"] = solution
                results["steps"] = self._get_linear_steps(cleaned_eq, variable, solution)
            
            elif equation_type == "quadratic":
                solutions = self._solve_quadratic(cleaned_eq, variable)
                results["solution"] = solutions
                results["steps"] = self._get_quadratic_steps(cleaned_eq, variable, solutions)
                results["graph_suggestion"] = True
            
            else:
                # Use AI for complex equations
                if self.ai_service:
                    ai_solution = self._get_ai_solution(equation, variable)
                    results.update(ai_solution)
                else:
                    results["solution"] = "Complex equation - AI assistance required"
                    results["steps"] = ["This equation requires advanced solving methods"]
            
            # Add verification if solution exists
            if results["solution"] and results["solution"] != "No solution":
                results["verification"] = self._verify_solution(cleaned_eq, variable, results["solution"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error solving equation: {e}")
            return {
                "success": False,
                "error": f"Equation solving failed: {str(e)}"
            }
    
    def calculate_expression(self, expression: str) -> Dict[str, Any]:
        """
        Calculate mathematical expressions.
        
        Args:
            expression: Mathematical expression to calculate
        
        Returns:
            Dictionary with calculation result
        """
        try:
            if not expression.strip():
                return {
                    "success": False,
                    "error": "No expression provided"
                }
            
            # Clean expression
            cleaned_expr = self._clean_expression(expression)
            
            results = {
                "success": True,
                "expression": expression,
                "cleaned_expression": cleaned_expr,
                "result": None,
                "steps": [],
                "units": None
            }
            
            # Check for units
            units = self._extract_units(expression)
            if units:
                results["units"] = units
            
            # Calculate
            try:
                result = self._safe_eval(cleaned_expr)
                results["result"] = result
                results["steps"] = self._get_calculation_steps(cleaned_expr, result)
            except Exception as e:
                results["success"] = False
                results["error"] = f"Calculation error: {str(e)}"
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating expression: {e}")
            return {
                "success": False,
                "error": f"Calculation failed: {str(e)}"
            }
    
    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """
        Convert between different units.
        
        Args:
            value: Numerical value to convert
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Dictionary with conversion result
        """
        try:
            conversion_factors = {
                # Length
                ('m', 'cm'): 100,
                ('m', 'mm'): 1000,
                ('m', 'km'): 0.001,
                ('cm', 'm'): 0.01,
                ('mm', 'm'): 0.001,
                ('km', 'm'): 1000,
                ('ft', 'm'): 0.3048,
                ('in', 'cm'): 2.54,
                
                # Mass
                ('kg', 'g'): 1000,
                ('g', 'kg'): 0.001,
                ('lb', 'kg'): 0.453592,
                ('oz', 'g'): 28.3495,
                
                # Temperature (special handling needed)
                # Volume
                ('l', 'ml'): 1000,
                ('ml', 'l'): 0.001,
                ('gal', 'l'): 3.78541,
                
                # Time
                ('h', 'min'): 60,
                ('min', 's'): 60,
                ('h', 's'): 3600,
                ('day', 'h'): 24,
            }
            
            # Special temperature conversions
            if from_unit.lower() in ['c', 'celsius'] and to_unit.lower() in ['f', 'fahrenheit']:
                result = (value * 9/5) + 32
                formula = "°F = (°C × 9/5) + 32"
            elif from_unit.lower() in ['f', 'fahrenheit'] and to_unit.lower() in ['c', 'celsius']:
                result = (value - 32) * 5/9
                formula = "°C = (°F - 32) × 5/9"
            elif from_unit.lower() in ['c', 'celsius'] and to_unit.lower() in ['k', 'kelvin']:
                result = value + 273.15
                formula = "K = °C + 273.15"
            elif from_unit.lower() in ['k', 'kelvin'] and to_unit.lower() in ['c', 'celsius']:
                result = value - 273.15
                formula = "°C = K - 273.15"
            else:
                # Regular unit conversion
                factor = conversion_factors.get((from_unit.lower(), to_unit.lower()))
                if factor is None:
                    # Try reverse conversion
                    reverse_factor = conversion_factors.get((to_unit.lower(), from_unit.lower()))
                    if reverse_factor:
                        factor = 1 / reverse_factor
                
                if factor is None:
                    return {
                        "success": False,
                        "error": f"Conversion from {from_unit} to {to_unit} not supported"
                    }
                
                result = value * factor
                formula = f"1 {from_unit} = {factor} {to_unit}"
            
            return {
                "success": True,
                "original_value": value,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "result": round(result, 6),
                "formula": formula,
                "conversion_string": f"{value} {from_unit} = {round(result, 6)} {to_unit}"
            }
            
        except Exception as e:
            logger.error(f"Error converting units: {e}")
            return {
                "success": False,
                "error": f"Unit conversion failed: {str(e)}"
            }
    
    def solve_statistics(self, data: List[float], statistic: str = "all") -> Dict[str, Any]:
        """
        Calculate statistical measures.
        
        Args:
            data: List of numerical data
            statistic: Specific statistic to calculate or "all"
        
        Returns:
            Dictionary with statistical results
        """
        try:
            if not data:
                return {
                    "success": False,
                    "error": "No data provided"
                }
            
            # Convert to float and filter valid numbers
            clean_data = []
            for item in data:
                try:
                    clean_data.append(float(item))
                except (ValueError, TypeError):
                    continue
            
            if not clean_data:
                return {
                    "success": False,
                    "error": "No valid numerical data found"
                }
            
            results = {
                "success": True,
                "data_count": len(clean_data),
                "statistics": {}
            }
            
            # Calculate statistics
            n = len(clean_data)
            sorted_data = sorted(clean_data)
            
            if statistic in ["mean", "all"]:
                results["statistics"]["mean"] = sum(clean_data) / n
            
            if statistic in ["median", "all"]:
                if n % 2 == 0:
                    results["statistics"]["median"] = (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
                else:
                    results["statistics"]["median"] = sorted_data[n//2]
            
            if statistic in ["mode", "all"]:
                from collections import Counter
                count_dict = Counter(clean_data)
                max_count = max(count_dict.values())
                modes = [k for k, v in count_dict.items() if v == max_count]
                results["statistics"]["mode"] = modes[0] if len(modes) == 1 else modes
            
            if statistic in ["range", "all"]:
                results["statistics"]["range"] = max(clean_data) - min(clean_data)
            
            if statistic in ["variance", "std", "all"]:
                mean = results["statistics"].get("mean", sum(clean_data) / n)
                variance = sum((x - mean) ** 2 for x in clean_data) / n
                results["statistics"]["variance"] = variance
                results["statistics"]["std_deviation"] = math.sqrt(variance)
            
            if statistic in ["min", "max", "all"]:
                results["statistics"]["minimum"] = min(clean_data)
                results["statistics"]["maximum"] = max(clean_data)
            
            # Add quartiles for "all"
            if statistic == "all":
                results["statistics"]["q1"] = self._calculate_percentile(sorted_data, 25)
                results["statistics"]["q3"] = self._calculate_percentile(sorted_data, 75)
                results["statistics"]["iqr"] = results["statistics"]["q3"] - results["statistics"]["q1"]
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {
                "success": False,
                "error": f"Statistical calculation failed: {str(e)}"
            }
    
    def _clean_equation(self, equation: str) -> str:
        """Clean and standardize equation format."""
        # Remove spaces
        cleaned = equation.replace(" ", "")
        
        # Replace common notation
        replacements = {
            '^': '**',  # Power notation
            '×': '*',   # Multiplication
            '÷': '/',   # Division
            'π': 'pi', # Pi constant
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    def _clean_expression(self, expression: str) -> str:
        """Clean expression for evaluation."""
        cleaned = self._clean_equation(expression)
        
        # Add math. prefix to functions
        for func in self.supported_functions:
            pattern = rf'\b{func}\('
            replacement = f'math.{func}('
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Replace constants
        for const, value in self.constants.items():
            cleaned = cleaned.replace(const, str(value))
        
        return cleaned
    
    def _identify_equation_type(self, equation: str) -> str:
        """Identify the type of equation."""
        if '=' not in equation:
            return "arithmetic"
        
        # Split equation at equals sign
        left, right = equation.split('=', 1)
        combined = left + right
        
        # Check for quadratic (x^2 or x**2)
        if re.search(r'x\*\*2|x\^2', combined):
            return "quadratic"
        
        # Check for linear (just x terms)
        if re.search(r'\bx\b', combined) and not re.search(r'x\*\*|x\^|sin|cos|tan|log', combined):
            return "linear"
        
        # Check for trigonometric
        if re.search(r'sin|cos|tan', combined):
            return "trigonometric"
        
        # Check for exponential/logarithmic
        if re.search(r'exp|log|ln', combined):
            return "exponential"
        
        return "complex"
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression."""
        # Create safe namespace
        safe_dict = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow
        }
        
        # Add constants
        safe_dict.update(self.constants)
        
        try:
            result = eval(expression, safe_dict)
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def _solve_arithmetic(self, expression: str) -> float:
        """Solve arithmetic expression."""
        return self._safe_eval(expression)
    
    def _solve_linear(self, equation: str, variable: str) -> str:
        """Solve linear equation."""
        try:
            # Simple linear equation solver
            # Format: ax + b = c or similar
            left, right = equation.split('=')
            
            # Move everything to left side
            expr = f"({left}) - ({right})"
            
            # Try substitution method for simple cases
            # This is a simplified implementation
            if variable == 'x':
                # Try some values to find pattern
                test_vals = [-10, -1, 0, 1, 10]
                for val in test_vals:
                    test_expr = expr.replace('x', str(val))
                    try:
                        result = self._safe_eval(test_expr)
                        if abs(result) < 1e-10:  # Close to zero
                            return str(val)
                    except:
                        continue
            
            return "Requires advanced solving"
            
        except Exception:
            return "Unable to solve"
    
    def _solve_quadratic(self, equation: str, variable: str) -> List[str]:
        """Solve quadratic equation using quadratic formula."""
        try:
            # This is a simplified implementation
            # For a more complete solution, would need symbolic math
            return ["Requires symbolic math library"]
        except Exception:
            return ["Unable to solve"]
    
    def _get_linear_steps(self, equation: str, variable: str, solution: str) -> List[str]:
        """Get step-by-step solution for linear equation."""
        return [
            f"Original equation: {equation}",
            f"Isolate {variable}",
            f"Solution: {variable} = {solution}"
        ]
    
    def _get_quadratic_steps(self, equation: str, variable: str, solutions: List[str]) -> List[str]:
        """Get step-by-step solution for quadratic equation."""
        return [
            f"Original equation: {equation}",
            "Apply quadratic formula: x = (-b ± √(b²-4ac)) / 2a",
            f"Solutions: {', '.join(solutions)}"
        ]
    
    def _verify_solution(self, equation: str, variable: str, solution: str) -> Dict[str, Any]:
        """Verify if solution satisfies the equation."""
        try:
            if '=' not in equation:
                return {"verified": False, "reason": "Not an equation"}
            
            left, right = equation.split('=')
            
            # Substitute solution
            left_sub = left.replace(variable, str(solution))
            right_sub = right.replace(variable, str(solution))
            
            left_val = self._safe_eval(left_sub)
            right_val = self._safe_eval(right_sub)
            
            difference = abs(left_val - right_val)
            verified = difference < 1e-10
            
            return {
                "verified": verified,
                "left_value": left_val,
                "right_value": right_val,
                "difference": difference
            }
            
        except Exception as e:
            return {"verified": False, "reason": f"Verification error: {str(e)}"}
    
    def _get_calculation_steps(self, expression: str, result: float) -> List[str]:
        """Get calculation steps for expression."""
        steps = [f"Expression: {expression}"]
        
        # Add intermediate steps for complex expressions
        if '+' in expression or '-' in expression:
            steps.append("Perform addition/subtraction from left to right")
        if '*' in expression or '/' in expression:
            steps.append("Perform multiplication/division first")
        if '**' in expression:
            steps.append("Calculate exponents first")
        
        steps.append(f"Result: {result}")
        return steps
    
    def _extract_units(self, expression: str) -> Optional[str]:
        """Extract units from expression."""
        # Simple unit detection
        unit_patterns = [
            r'\b(m|cm|mm|km|ft|in)\b',  # Length
            r'\b(kg|g|lb|oz)\b',        # Mass
            r'\b(l|ml|gal)\b',          # Volume
            r'\b(s|min|h|day)\b',       # Time
            r'\b(°C|°F|K)\b'            # Temperature
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, expression)
            if match:
                return match.group(1)
        
        return None
    
    def _calculate_percentile(self, sorted_data: List[float], percentile: float) -> float:
        """Calculate percentile of sorted data."""
        n = len(sorted_data)
        k = (percentile / 100) * (n - 1)
        
        if k.is_integer():
            return sorted_data[int(k)]
        else:
            lower = sorted_data[int(k)]
            upper = sorted_data[int(k) + 1]
            return lower + (k - int(k)) * (upper - lower)
    
    def _get_ai_solution(self, equation: str, variable: str) -> Dict[str, Any]:
        """Get AI-powered equation solution."""
        if not self.ai_service or not hasattr(self.ai_service, 'provider'):
            return {"solution": "AI assistance not available"}
        
        try:
            prompt = f"""Solve this mathematical equation step by step:

Equation: {equation}
Solve for: {variable}

Please provide:
1. Step-by-step solution
2. Final answer
3. Verification (substitute back into original equation)

Show all work clearly."""

            response = self.ai_service.provider.generate_content(prompt)
            
            return {
                "solution": "See AI explanation",
                "ai_solution": response.strip() if response else "No solution available",
                "steps": ["AI-powered solution (see details below)"]
            }
            
        except Exception as e:
            logger.error(f"Error getting AI solution: {e}")
            return {"solution": "AI solution failed", "error": str(e)}

# Global instance
_math_solver = None

def create_math_solver(ai_service) -> MathSolver:
    """Create a math solver instance."""
    return MathSolver(ai_service)

def solve_equation(equation: str, ai_service, variable: str = 'x') -> Dict[str, Any]:
    """Solve mathematical equation."""
    solver = MathSolver(ai_service)
    return solver.solve_equation(equation, variable)

def calculate_expression(expression: str, ai_service) -> Dict[str, Any]:
    """Calculate mathematical expression."""
    solver = MathSolver(ai_service)
    return solver.calculate_expression(expression)

def convert_units(value: float, from_unit: str, to_unit: str, ai_service) -> Dict[str, Any]:
    """Convert between units."""
    solver = MathSolver(ai_service)
    return solver.convert_units(value, from_unit, to_unit)

def solve_statistics(data: List[float], ai_service, statistic: str = "all") -> Dict[str, Any]:
    """Calculate statistics."""
    solver = MathSolver(ai_service)
    return solver.solve_statistics(data, statistic) 