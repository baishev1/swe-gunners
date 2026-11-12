import 'package:flutter/material.dart';
import 'package:forui/forui.dart';

FThemeData staffTheme(Brightness brightness) {
  final dark = brightness == Brightness.dark;
  final colors = (dark ? FColors.neutralDark : FColors.neutralLight).copyWith(
    background: dark ? const Color(0xFF10191D) : const Color(0xFFF5F7F7),
    foreground: dark ? const Color(0xFFEAF0F0) : const Color(0xFF172B32),
    primary: dark ? const Color(0xFF81D5BA) : const Color(0xFF166B55),
    primaryForeground: dark ? const Color(0xFF102E25) : const Color(0xFFFFFFFF),
    secondary: dark ? const Color(0xFF243339) : const Color(0xFFE8EEED),
    secondaryForeground: dark
        ? const Color(0xFFEAF0F0)
        : const Color(0xFF172B32),
    muted: dark ? const Color(0xFF1B292F) : const Color(0xFFEDF1F1),
    mutedForeground: dark ? const Color(0xFFABB9BD) : const Color(0xFF566B72),
    card: dark ? const Color(0xFF19262C) : const Color(0xFFFFFFFF),
    border: dark ? const Color(0xFF314148) : const Color(0xFFDEE5E5),
  );
  return FThemeData(touch: true, colors: colors);
}

ThemeData materialTheme(FThemeData theme) {
  final base = theme.toApproximateMaterialTheme();
  return base.copyWith(
    scaffoldBackgroundColor: theme.colors.background,
    cardColor: theme.colors.card,
    appBarTheme: AppBarTheme(
      backgroundColor: theme.colors.background,
      foregroundColor: theme.colors.foreground,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 17,
        fontWeight: FontWeight.w600,
        color: theme.colors.foreground,
      ),
    ),
    textTheme: base.textTheme.copyWith(
      headlineLarge: TextStyle(
        fontSize: 32,
        height: 1.15,
        letterSpacing: -1,
        fontWeight: FontWeight.w700,
        color: theme.colors.foreground,
      ),
      headlineMedium: TextStyle(
        fontSize: 28,
        height: 1.2,
        letterSpacing: -0.7,
        fontWeight: FontWeight.w700,
        color: theme.colors.foreground,
      ),
      titleLarge: TextStyle(
        fontSize: 20,
        height: 1.3,
        letterSpacing: -0.3,
        fontWeight: FontWeight.w600,
        color: theme.colors.foreground,
      ),
      bodyLarge: TextStyle(
        fontSize: 16,
        height: 1.5,
        color: theme.colors.foreground,
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        height: 1.45,
        color: theme.colors.foreground,
      ),
      bodySmall: TextStyle(
        fontSize: 12,
        height: 1.4,
        color: theme.colors.mutedForeground,
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: theme.colors.card,
      indicatorColor: theme.colors.secondary,
      height: 72,
      labelTextStyle: WidgetStatePropertyAll(
        TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: theme.colors.foreground,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          size: 24,
          color: states.contains(WidgetState.selected)
              ? theme.colors.primary
              : theme.colors.mutedForeground,
        ),
      ),
    ),
    dividerColor: theme.colors.border,
  );
}
