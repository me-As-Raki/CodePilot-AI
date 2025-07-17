;; ========== FUNCTIONS ==========
(function_definition
  declarator: (function_declarator
    declarator: (identifier) @function.name))

;; ========== FUNCTION PROTOTYPES ==========
(declaration
  type: (_)
  declarator: (function_declarator
    declarator: (identifier) @prototype.name))

;; ========== STRUCTS ==========
(struct_specifier
  name: (type_identifier) @struct.name)

;; ========== TYPEDEFS ==========
(type_definition
  type: (_)
  declarator: (type_identifier) @typedef.name)

;; ========== ENUMS ==========
(enum_specifier
  name: (type_identifier) @enum.name)

;; ========== MACROS ==========
(preproc_def
  name: (identifier) @macro.name)

;; ========== FUNCTION-LIKE MACROS ==========
(preproc_function_def
  name: (identifier) @macro.name)

;; ========== GLOBAL VARIABLES ==========
(declaration
  type: (_)
  declarator: (init_declarator
    declarator: (identifier) @global.name))

;; ========== INCLUDES ==========
(preproc_include
  path: (preproc_arg) @preproc.name)

