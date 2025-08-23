// Utility functions for date formatting

export const formatDate = (dateString: string | null | undefined, options?: Intl.DateTimeFormatOptions): string => {
  if (!dateString) return 'Not available';
  
  try {
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    
    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    
    return date.toLocaleDateString('en-US', options || defaultOptions);
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid date';
  }
};

export const formatDateTime = (dateString: string | null | undefined): string => {
  return formatDate(dateString, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDateShort = (dateString: string | null | undefined): string => {
  return formatDate(dateString, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};