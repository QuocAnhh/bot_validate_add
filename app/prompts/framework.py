"""Prompt framework for building agent prompts with template variables"""
from typing import Dict, Any, Optional
from pathlib import Path
import re


class PromptFramework:
    """Prompt framework for building agent prompts with template variables"""
    
    # Prompt sections
    ROLE_AND_OBJECTIVE = """# 1. ROLE & OBJECTIVE - Vai trò và mục tiêu
Bạn là {{AGENT.NAME}}, {{AGENT.DESCRIPTION}}
{{role_and_objective}}"""

    COMMUNICATION_STYLE = """# 2. COMMUNICATION STYLE - Phong cách giao tiếp
{{communication_style}}
# 2.1 Greeting - Lời chào
{{AGENT.START_MESSAGE}}
# 2.2 Ending - Lời kết thúc
{{AGENT.END_MESSAGE}}"""

    TOOLS_DESCRIPTION = """# 3. TOOLS AVAILABLE - Các công cụ có sẵn
{{tools_description}}"""

    MEMORY_INSTRUCTIONS = """# 4. MEMORY INSTRUCTIONS - Hướng dẫn về bộ nhớ
{{memory_instructions}}"""

    OUTPUT_FORMAT = """# 5. OUTPUT FORMAT - Định dạng đầu ra
{{output_format}}"""

    STANDARD_FLOW = """# 6. STANDARD FLOW - Quy trình chuẩn
{{standard_flow}}"""

    CORE_RULES = """# 7. CORE RULES - Quy tắc cốt lõi
{{core_rules}}"""

    SAMPLE_EXCHANGES = """# 8. SAMPLE EXCHANGES - Mẫu đối thoại
{{sample_exchanges}}"""

    FINAL_INSTRUCTIONS = """# 9. FINAL INSTRUCTIONS - Hướng dẫn cuối cùng
{{final_instructions}}"""

    # Default prompt template
    DEFAULT_PROMPT_TEMPLATE = """{{ROLE_AND_OBJECTIVE}}

{{COMMUNICATION_STYLE}}

{{TOOLS_DESCRIPTION}}

{{MEMORY_INSTRUCTIONS}}

{{STANDARD_FLOW}}

{{CORE_RULES}}

{{SAMPLE_EXCHANGES}}

{{OUTPUT_FORMAT}}

{{FINAL_INSTRUCTIONS}}
"""

    @staticmethod
    def replace_variables(template: str, variables: Dict[str, Any]) -> str:
        """
        Replace template variables with actual values
        
        Args:
            template: Template string with {{VARIABLE}} placeholders
            variables: Dictionary of variable values
            
        Returns:
            String with variables replaced
        """
        result = template
        
        # Replace nested variables like {{AGENT.NAME}}
        def replace_nested(match):
            var_path = match.group(1)
            parts = var_path.split('.')
            value = variables
            try:
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part, match.group(0))
                    else:
                        return match.group(0)
                return str(value) if value is not None else ""
            except (KeyError, AttributeError, TypeError):
                return match.group(0)
        
        # Replace {{VARIABLE}} patterns
        result = re.sub(r'\{\{([^}]+)\}\}', replace_nested, result)
        
        return result
    
    @staticmethod
    def load_template(template_path: str) -> str:
        """
        Load prompt template from file
        
        Args:
            template_path: Path to template file
            
        Returns:
            Template content as string
        """
        template_file = Path(template_path)
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def build_prompt(
        template_path: Optional[str] = None,
        template_content: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build final prompt from template and variables
        
        Args:
            template_path: Path to template file (or use template_content)
            template_content: Template content as string (or use template_path)
            variables: Dictionary of variables to replace
            
        Returns:
            Final prompt with variables replaced
        """
        # Load template
        if template_path:
            template = PromptFramework.load_template(template_path)
        elif template_content:
            template = template_content
        else:
            template = PromptFramework.DEFAULT_PROMPT_TEMPLATE
        
        # Replace variables
        if variables:
            template = PromptFramework.replace_variables(template, variables)
        
        return template
    
    @staticmethod
    def format_tools_description(tools: list) -> str:
        """
        Format tools list into description text
        
        Args:
            tools: List of tool configs
            
        Returns:
            Formatted tools description
        """
        if not tools:
            return "Không có công cụ nào được cấu hình."
        
        description = "Bạn có các công cụ sau đây:\n\n"
        
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('name', f'Tool {i}')
            tool_desc = tool.get('description', '')
            
            description += f"{i}. **{tool_name}**: {tool_desc}\n"
            
            # Add parameters if available
            params = tool.get('parameters', {})
            if params and isinstance(params, dict):
                props = params.get('properties', {})
                if props:
                    description += "   Tham số:\n"
                    for param_name, param_info in props.items():
                        param_desc = param_info.get('description', '')
                        param_type = param_info.get('type', 'string')
                        description += f"   - {param_name} ({param_type}): {param_desc}\n"
            
            description += "\n"
        
        return description
    
    @staticmethod
    def format_memory_instructions(memory_config: Dict[str, Any]) -> str:
        """
        Format memory instructions based on config
        
        Args:
            memory_config: Memory configuration
            
        Returns:
            Formatted memory instructions
        """
        if not memory_config.get('enabled', False):
            return "Bộ nhớ (Memory) hiện chưa được kích hoạt."
        
        memory_type = memory_config.get('type', 'non_parametric')
        top_k = memory_config.get('top_k', 4)
        
        instructions = f"""Bộ nhớ (Memory) đã được kích hoạt với loại: {memory_type}.
Bạn sẽ được cung cấp {top_k} trường hợp tương tự từ lịch sử để tham khảo.
Hãy sử dụng các trường hợp này để cải thiện phản hồi của bạn."""
        
        return instructions


# Convenience functions
def load_prompt(template_path: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """Load and build prompt from template file"""
    return PromptFramework.build_prompt(template_path=template_path, variables=variables)


def build_prompt_from_content(
    template_content: str,
    variables: Optional[Dict[str, Any]] = None
) -> str:
    """Build prompt from template content"""
    return PromptFramework.build_prompt(template_content=template_content, variables=variables)

