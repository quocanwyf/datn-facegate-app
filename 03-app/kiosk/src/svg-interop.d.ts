import 'react-native-svg';

// Phosphor 3 adds this optional web metadata when importing individual icons.
// SVG native rendering does not use the class; the app styles icons via props.
declare module 'react-native-svg' {
  interface SvgProps {
    className?: string;
  }
}
