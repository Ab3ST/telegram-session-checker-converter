class Theme:
    LIGHT = {
        'main_bg': '#f8f9fa',
        'sidebar_bg': '#ffffff',
        'sidebar_border': '#e9ecef',
        'button_bg': 'transparent',
        'button_hover': '#f0f0f0',
        'button_active': '#4a90e2',
        'button_text': '#495057',
        'button_text_active': '#ffffff',
        'dialog_bg': '#ffffff',
        'input_bg': '#ffffff',
        'input_border': '#ced4da',
        'input_focus': '#4a90e2',
        'text_primary': '#212529',
        'text_secondary': '#6c757d',
        'border': '#e9ecef',
        'shadow': 'rgba(0, 0, 0, 0.1)',
        'log_bg': '#ffffff',
        'log_border': '#dee2e6',
        'success': '#28a745',
        'error': '#dc3545',
        'info': '#17a2b8',
        'card_bg': '#ffffff',
        'divider': '#e9ecef',
    }
    
    DARK = {
        'main_bg': '#1e1e1e',
        'sidebar_bg': '#252526',
        'sidebar_border': '#3e3e42',
        'button_bg': 'transparent',
        'button_hover': '#323233',
        'button_active': '#0e639c',
        'button_text': '#cccccc',
        'button_text_active': '#ffffff',
        'dialog_bg': '#252526',
        'input_bg': '#3c3c3c',
        'input_border': '#5a5a5a',
        'input_focus': '#007acc',
        'text_primary': '#cccccc',
        'text_secondary': '#858585',
        'border': '#3e3e42',
        'shadow': 'rgba(0, 0, 0, 0.5)',
        'log_bg': '#1e1e1e',
        'log_border': '#3e3e42',
        'success': '#4ec9b0',
        'error': '#f48771',
        'info': '#4fc3f7',
        'card_bg': '#252526',
        'divider': '#3e3e42',
    }
    
    @staticmethod
    def get_main_window_style(colors):
        return f"""
            QMainWindow {{
                background: {colors['main_bg']};
            }}
        """
    
    @staticmethod
    def get_sidebar_button_style(colors):
        return f"""
            QPushButton {{
                background: {colors['button_bg']};
                color: {colors['button_text']};
                border: none;
                text-align: left;
                padding-left: 25px;
                font-size: 10pt;
            }}
            QPushButton:!checked:hover {{
                background: {colors['button_hover']};
            }}
            QPushButton:checked {{
                background: {colors['button_active']};
                color: {colors['button_text_active']};
                font-weight: 500;
            }}
        """
    
    @staticmethod
    def get_theme_button_style(colors):
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                padding: 10px;
                color: {colors['text_secondary']};
            }}
            QPushButton:hover {{
                background: {colors['button_hover']};
                color: {colors['text_primary']};
            }}
        """
    
    @staticmethod
    def get_content_style(colors):
        return f"background: {colors['main_bg']};"
    
    @staticmethod
    def get_card_style(colors):
        return f"""
            QWidget {{
                background: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
            }}
        """
    
    @staticmethod
    def get_dialog_style(colors):
        return f"""
            QDialog {{
                background: {colors['dialog_bg']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {colors['text_primary']};
                background: transparent;
            }}
            QScrollArea {{
                border: none;
                background: {colors['dialog_bg']};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {colors['input_bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['input_border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {colors['input_focus']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
    
    @staticmethod
    def get_input_style(colors):
        return f"""
            QLineEdit {{
                background: {colors['input_bg']};
                border: 1px solid {colors['input_border']};
                border-radius: 4px;
                padding: 0 10px;
                color: {colors['text_primary']};
                font-size: 9pt;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['input_focus']};
                background: {colors['input_bg']};
            }}
        """
    
    @staticmethod
    def get_button_style(colors):
        return f"""
            QPushButton {{
                background: {colors['button_active']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: #357abd;
            }}
            QPushButton:pressed {{
                background: #2868a8;
            }}
            QPushButton:disabled {{
                background: {colors['border']};
                color: {colors['text_secondary']};
            }}
        """
    
    @staticmethod
    def get_radio_style(colors):
        return f"""
            QRadioButton {{
                color: {colors['text_primary']};
                spacing: 8px;
                background: transparent;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {colors['input_border']};
                background: {colors['input_bg']};
            }}
            QRadioButton::indicator:hover {{
                border-color: {colors['input_focus']};
            }}
            QRadioButton::indicator:checked {{
                background: {colors['button_active']};
                border-color: {colors['button_active']};
            }}
        """
    
    @staticmethod
    def get_combobox_style(colors):
        return f"""
            QComboBox {{
                background: {colors['input_bg']};
                border: 1px solid {colors['input_border']};
                border-radius: 4px;
                padding: 0 10px;
                color: {colors['text_primary']};
            }}
            QComboBox:hover {{
                border-color: {colors['input_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
            }}
            QComboBox QAbstractItemView {{
                background: {colors['dialog_bg']};
                border: 1px solid {colors['input_border']};
                selection-background-color: {colors['button_active']};
                selection-color: #ffffff;
                color: {colors['text_primary']};
            }}
        """
    
    @staticmethod
    def get_error_input_style():
        return """
            QLineEdit {
                background: #fff5f5;
                border: 2px solid #dc3545;
                border-radius: 4px;
                padding: 0 10px;
                color: #495057;
                font-size: 9pt;
            }
        """
