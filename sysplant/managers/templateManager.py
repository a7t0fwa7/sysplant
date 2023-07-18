# -*- coding:utf-8 -*-
import json

import importlib.resources as pkg_resources

from sysplant import data as pkg_data
from sysplant import templates as pkg_templates
from sysplant.templates import iterators as pkg_iterators
from sysplant.templates import resolvers as pkg_resolvers
from sysplant.templates import stubs as pkg_stubs

from sysplant.constants.sysplantConstants import SysPlantConstants
from sysplant.abstracts.abstractFactory import AbstractFactory
from sysplant.managers.nimGenerator import NIMGenerator


class TemplateManager(AbstractFactory):
    """
    Main class responsible for template handling: tag replacement or erase with content generated by __coder bot

    Args:
        AbstractFactory (_type_): AbstractClass defining useful functions potentially reusable by other classes
    """

    def __init__(
        self, arch: str = "x64", syscall: str = "syscall", language: str = "nim"
    ) -> None:
        """
        Init method.
        Will instanciate appropriate self.__coder var depending on the language selected responsible for code generation

        Args:
            arch (str, optional): Code architecture to generate. Defaults to "x64".
            syscall (str, optional): Syscall instruction to use. Defaults to "syscall".
            language (str, optional): Language type used by code generator. Defaults to "nim".

        Raises:
            NotImplementedError: Error raised when using unsupported architecture
            NotImplementedError: Error raised when using unsupported syscall instruction
            NotImplementedError: Error raised when using unsupported language
            SystemError: Error raised when unable to load protoypes.json
            SystemError: Error raised when unable to load base template for language specify
        """
        super().__init__()

        # Define language template
        if arch not in ["x86", "x64", "wow"]:
            raise NotImplementedError("Sorry architecture not implemented yet")
        if language not in ["nim"]:
            raise NotImplementedError("Sorry language not supported ... yet ?!")
        if syscall not in ["syscall", "sysenter", "int 0x2h"]:
            raise NotImplementedError(
                "Sorry syscall instruction not supported ... yet ?!"
            )

        self.__lang = language
        self.__arch = arch
        self.__syscall = syscall

        # Set coder bot
        if self.__lang == "nim":
            self.__coder = NIMGenerator()

        try:
            # Alaways load prototypes & typedefinitions
            self.__load_prototypes()
        except Exception as err:
            raise SystemError(f"Unable to load prototypes: {err}")

        try:
            # Always load initial template
            self.data = self.__load_template(pkg_templates, f"base.{self.__lang}")
        except Exception as err:
            raise SystemError(f"Unable to load base template: {err}")

        # Initialize seed
        self.__seed = self.generate_random_seed()

    def __str__(self) -> str:
        return self.data

    def __load_template(self, pkg_module: str, name: str) -> str:
        """Private method used to retrieve specific data file from package module

        Args:
            pkg_module (str): The package module containing filename to request
            name (str): Filename to request

        Raises:
            ValueError: Error raised if name is None
            ValueError: Error raised if name contains forbidden chars

        Returns:
            str: Return the file content (text mode)
        """
        if name is None:
            raise ValueError("Template name can not be null")

        # Check only extension dot is set
        if not name.replace(".", "", 1).replace(f"_{self.__arch}", "", 1).isalnum():
            raise ValueError("Invalid template name")

        # Adapt module based on what to load
        raw = pkg_resources.open_text(pkg_module, name)
        return raw.read()

    def __load_prototypes(self) -> None:
        """
        Private method used to load the prototypes file containing all the windows functions and their parameters (name and type).
        JSON dictionnary will be loaded once at init in private self.__prototypes for future use.
        """
        # Load supported functions prototypes
        data = self.__load_template(pkg_data, "prototypes.json")
        self.__prototypes = json.loads(data)

    def load_stub(self, name) -> str:
        """
        Public method used to load stub pattern file from package

        Args:
            name (_type_): Stub name to use

        Raises:
            SystemError: Error raised if filename does not exists

        Returns:
            str: File content (text mode)
        """
        try:
            # Load initial stub template
            self.data = self.__load_template(pkg_stubs, f"{name}.{self.__lang}")
        except Exception as err:
            raise SystemError(f"Unable to load {name} stub: {err}")

        return self.data

    def list_supported_syscalls(self) -> list:
        """
        Public method used to retrieve all supported functions names defined in prototypes.json

        Returns:
            list: List of NtFunctions names
        """
        return self.__prototypes.keys()

    def list_common_syscalls(self) -> list:
        """
        Public method used to retrieve most common functions names defined in prototypes.json

        Returns:
            list: List of NtFunctions names
        """
        return SysPlantConstants.COMMON_SYSCALLS

    def list_donut_syscalls(self) -> list:
        """
        Public method used to retrieve functions names defined in prototypes.json used by Donut project (stay tuned for HOMER project ... ;) )

        Returns:
            list: List of NtFunctions names
        """
        return SysPlantConstants.DONUT_SYSCALLS

    def set_debug(self) -> str:
        """
        Public method used to generate the language specific code of DEBUG flag definition.
        Is debug is not set it will erase the tag from template.
        The debug definition code is then used to replace the SPT_DEBUG tag in template.

        Returns:
            str: Template content after modification
        """
        if self.logger.isDebug():
            # Generate debug constant based on log level condition
            debug_const = self.__coder.generate_debug(True)
            self.replace_tag("SPT_DEBUG", debug_const)
        else:
            self.remove_tag("SPT_DEBUG")

        return self.data

    def set_seed(self, seed: int = 0) -> str:
        """
        Public method used to generate the language specific code of SEED value definition.
        The seed parameter is optional and if omitted it will be automatically generated with a random value.
        The seed definition code is then used to replace the SPT_SEED tag in template.

        Args:
            seed (int, optional): Seed value. Defaults to 0.

        Returns:
            str: Template content after modification
        """
        if seed != 0:
            self.__seed = seed

        # Set SEED declaration
        seed_code = self.__coder.generate_seed(self.__seed)
        self.replace_tag("SPT_SEED", seed_code)

        return self.data

    def set_iterator(self, name: str) -> str:
        """
        Public method used to retrieve the language specific code of Syscall retrieval iterator.
        The selected iterator is then used to replace the SPT_ITERATOR tag in template.

        Args:
            name (str): Iterator name to use

        Returns:
            str: Template content after modification
        """
        # Get iterator template from package
        data = self.__load_template(pkg_iterators, f"{name}.{self.__lang}")
        self.replace_tag("SPT_ITERATOR", data)

        return self.data

    def set_resolver(self, name: str) -> str:
        """
        Public method used to retrieve the language specific code of NtFunction resolver based on hash value.
        The selected resolver is then used to replace the SPT_RESOLVER tag in template.

        Args:
            name (str): Resolver name to use

        Returns:
            str: Template content after modification
        """
        # Get resolver template from package
        data = self.__load_template(pkg_resolvers, f"{name}.{self.__lang}")
        self.replace_tag("SPT_RESOLVER", data)

        return self.data

    def set_caller(self, name: str, resolver: str) -> str:
        """
        Public method used to retrieve the language specific code of the main call function.
        The caller code is adapted with correct resolver function name (using FUNCTION_RESOLVE tag)
        The caller code is adapted with correct syscall instruction (using SYSCALL_INT tag)
        The caller code embbed interuption (int 3) in case of DEBUG state (using DUBG_INT tag)
        The selected caller is then used to replace the SPT_CALLER tag in template.

        Args:
            name (str): Caller name to use
            resolver (str): Resolver name to use

        Returns:
            str: Template content after modification
        """
        # Get caller function from package
        data = self.__load_template(pkg_stubs, f"{name}_{self.__arch}.{self.__lang}")
        self.replace_tag("SPT_CALLER", data)

        # Replace resolver functions in stub
        func_resolver = (
            "SPT_GetRandomSyscallAddress"
            if resolver == "random"
            else "SPT_GetSyscallAddress"
        )

        # Adapt caller with proper options
        self.replace_tag("FUNCTION_RESOLVE", func_resolver)
        self.replace_tag("SYSCALL_INT", self.__syscall)

        # Set debug interruption on debug state
        if self.logger.isDebug():
            self.replace_tag("DEBUG_INT", "int 3")
        else:
            self.remove_tag("DEBUG_INT")

        return self.data

    def __generate_definitions(self) -> str:
        """
        Private method used to generate the type definitions required by NtFunctions list specified to generate_stubs().
        Generated code is then used to replace the TYPE_DEFINITIONS tag in template.

        Returns:
            str: Template content after modification
        """
        code = self.__coder.generate_definitions()
        self.replace_tag("TYPE_DEFINITIONS", code)

        return self.data

    def generate_stubs(self, names: list) -> str:
        """
        Public method used to generate stubs for all the NtFunctions to hook.
        Once generated a call is made to self.__generate_definitions() for automated type definitions.
        Generated code is then used to replace the SPT_STUBS tag in template.

        Args:
            names (list): List of NtFunctions to hook

        Raises:
            NotImplementedError: Error raised if NtFunction is not supported

        Returns:
            str: Template content after modification
        """
        self.logger.debug(
            f"\t. Hooking selected functions: {','.join(names)}", stripped=True
        )
        stubs_code = ""

        # Resolve all headers for functions to hook
        for n in names:
            params = self.__prototypes.get(n)
            # Avoid unsupported functions
            if params is None:
                raise NotImplementedError(f"Unsupported syscall {n}")

            # Calculate function hash
            fhash = self.get_function_hash(self.__seed, n)

            # Generate stub
            stubs_code += self.__coder.generate_stub(n, params, fhash)

        # Replace syscall stubs
        self.replace_tag("SPT_STUBS", stubs_code)

        # Auto generate required definitions
        self.__generate_definitions()

        return self.data

    def scramble(self) -> str:
        """
        Public method used to randomize fixed internal function names to avoid static analysis by EDR/AV.
        Note: The concept behind this method is to let another project randomize the NtFunctions names as Sysplant as no view of the code using it.

        Returns:
            str: Template content after modification
        """
        generated = set()
        for name in SysPlantConstants.INTERNAL_FUNCTIONS:
            randomized = self.generate_random_string(SysPlantConstants.RANDOM_WORD_SIZE)
            # Avoid function collisions
            while randomized in generated:
                randomized = self.generate_random_string(
                    SysPlantConstants.RANDOM_WORD_SIZE
                )

            # Store already set function name
            generated.add(randomized)

            # Replace name in code
            self.data = self.data.replace(name, randomized)

        return self.data
