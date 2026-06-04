package com.example.mantenimientoapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.mantenimientoapp.ui.admin.AdminScreen
import com.example.mantenimientoapp.ui.admin.equipos.EquiposAdminScreen
import com.example.mantenimientoapp.ui.admin.programas.ProgramasAdminScreen
import com.example.mantenimientoapp.ui.admin.repuestos.RepuestosAdminScreen
import com.example.mantenimientoapp.ui.admin.tecnicos.TecnicosAdminScreen
import com.example.mantenimientoapp.ui.auth.LoginScreen
import com.example.mantenimientoapp.ui.auth.LoginViewModel
import com.example.mantenimientoapp.ui.cronograma.CronogramaScreen
import com.example.mantenimientoapp.ui.home.HomeScreen
import com.example.mantenimientoapp.ui.ordenes.OrdenDetailScreen
import com.example.mantenimientoapp.ui.settings.SettingsScreen

object Routes {
    const val LOGIN = "login"
    const val HOME = "home"
    const val ORDEN_DETAIL = "orden/{id}"
    const val ADMIN_EQUIPOS = "admin/equipos"
    const val ADMIN_PROGRAMAS = "admin/programas"
    const val ADMIN_REPUESTOS = "admin/repuestos"
    const val ADMIN_TECNICOS = "admin/tecnicos"

    fun ordenDetail(id: Int) = "orden/$id"
}

@Composable
fun AppNavigation(navController: NavHostController) {
    val loginVm: LoginViewModel = hiltViewModel()
    val isLoggedIn by loginVm.isLoggedIn.collectAsState(initial = false)

    NavHost(
        navController = navController,
        startDestination = if (isLoggedIn) Routes.HOME else Routes.LOGIN
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(onLoginSuccess = {
                navController.navigate(Routes.HOME) {
                    popUpTo(Routes.LOGIN) { inclusive = true }
                }
            })
        }

        composable(Routes.HOME) {
            HomeScreen(
                onOrdenClick = { id -> navController.navigate(Routes.ordenDetail(id)) },
                onNavigateToAdminEquipos = { navController.navigate(Routes.ADMIN_EQUIPOS) },
                onNavigateToAdminProgramas = { navController.navigate(Routes.ADMIN_PROGRAMAS) },
                onNavigateToAdminRepuestos = { navController.navigate(Routes.ADMIN_REPUESTOS) },
                onNavigateToAdminTecnicos = { navController.navigate(Routes.ADMIN_TECNICOS) },
                onLogout = {
                    navController.navigate(Routes.LOGIN) {
                        popUpTo(Routes.HOME) { inclusive = true }
                    }
                }
            )
        }

        composable(
            route = Routes.ORDEN_DETAIL,
            arguments = listOf(navArgument("id") { type = NavType.IntType })
        ) { backStack ->
            val ordenId = backStack.arguments!!.getInt("id")
            OrdenDetailScreen(
                ordenId = ordenId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Routes.ADMIN_EQUIPOS) {
            EquiposAdminScreen(onBack = { navController.popBackStack() })
        }
        composable(Routes.ADMIN_PROGRAMAS) {
            ProgramasAdminScreen(onBack = { navController.popBackStack() })
        }
        composable(Routes.ADMIN_REPUESTOS) {
            RepuestosAdminScreen(onBack = { navController.popBackStack() })
        }
        composable(Routes.ADMIN_TECNICOS) {
            TecnicosAdminScreen(onBack = { navController.popBackStack() })
        }
    }
}
