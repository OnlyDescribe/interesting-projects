add_rules("mode.release", "mode.releasedbg", "mode.debug")

if is_plat("linux") then
    add_cxflags("-m64")
    add_cxflags("-std=c++17")
    -- set_symbols("debug")
    add_requires("gmp","ntl","flint",{system=true})
end

add_requires("Singular")

package("Singular")
    set_sourcedir(path.join(os.scriptdir(), "Singular"))
    add_deps("autoconf", "automake", "libtool", "pkg-config")
    on_load(function (package)
        package:add("includedirs", "include/singular")
        package:add("includedirs", "include")
    end)
    on_install(function (package)
        local configs = {}
        table.insert(configs, "--enable-streamio")
        table.insert(configs, "--enable-debug")
        table.insert(configs, "--with-track-fl")
        table.insert(configs, "--with-track-backtrace")
        import("package.tools.autoconf").install(package, configs)
    end)

target("main")
    set_enabled(true)
    set_kind("binary")
    if is_mode("debug") then
    add_defines("DEBUG")
    end
    add_defines("TIMING")
    -- add_includedirs("include","include/singular")
    add_includedirs("src")
    add_files("main.cc","src/test.cc")
    add_rpathdirs("$ORIGIN/lib")
    add_packages("Singular")

    -- add_links("Singular")
    -- add_linkdirs("") 