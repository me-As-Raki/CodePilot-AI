;; Match C function names
(function_definition
  declarator: (function_declarator
    declarator: (identifier) @function.name))
