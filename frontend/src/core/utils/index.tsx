class Utils {
  /**
   * Convert file size from bytes to a human-readable format (KB, MB, GB, etc.).
   * @param bytes - The file size in bytes.
   * @returns {string} - The formatted file size.
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return "0 Bytes";
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + " " + sizes[i];
  }

  /**
   * Format a Date object as "YYYY-MM-DD".
   * @param date - The date to format.
   * @returns {string} - The formatted date string.
   */
  static formatDate(date: Date, showTime: boolean = false): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    if (!showTime) return `${year}-${month}-${day}`;
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  }

  /**
   * Returns a human-readable "time ago" string for a given date.
   * @param dateInput - A Date object or a date string.
   * @returns {string} - e.g., "2 days ago", "Just now", etc.
   */
  static timeAgo(dateInput: Date | string): string {

    if(!dateInput) return '';
    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    let interval = Math.floor(seconds / 31536000);
    if (interval >= 1) {
      return `${interval} year${interval > 1 ? 's' : ''} ago`;
    }

    interval = Math.floor(seconds / 2592000);
    if (interval >= 1) {
      return `${interval} month${interval > 1 ? 's' : ''} ago`;
    }

    interval = Math.floor(seconds / 86400);
    if (interval >= 1) {
      return `${interval} day${interval > 1 ? 's' : ''} ago`;
    }

    interval = Math.floor(seconds / 3600);
    if (interval >= 1) {
      return `${interval} hour${interval > 1 ? 's' : ''} ago`;
    }

    interval = Math.floor(seconds / 60);
    if (interval >= 1) {
      return `${interval} minute${interval > 1 ? 's' : ''} ago`;
    }

    return "Just now";
  }

  static nl2br(text : String) {
    // Escape HTML special characters
    const escapedText = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    // Replace newline characters with <br>
    return escapedText.replace(/\n/g, '<br />');
  }

  static downloadMessage(message: any): void {
    console.log("Download clicked for message:", message);
    const element = document.createElement("a");
    const file = new Blob([message.text], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = `message-${message.id}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  // Copies the entire content of the message container to the clipboard.
  static copyMessage(message: any): void {
    const messageElement = document.getElementById(`message_${message.id}`);
    if (!messageElement) {
      console.error("Message element not found");
      return;
    }
    // Use innerText to copy plain text content.
    const textToCopy = messageElement.innerText;
    navigator.clipboard
      .writeText(textToCopy)
      .then(() => {
        console.log("Content copied to clipboard");
      })
      .catch((err) => {
        console.error("Failed to copy content:", err);
      });
  }

  /**
   * Capitalizes the first letter of each word and replaces hyphens with spaces.
   * @param text - The input text to format.
   * @returns {string} - The formatted text with capitalized words and spaces instead of hyphens.
   */
  static capitalizeWords(text: string): string {
    if (!text) return '';
    return text
      .replace(/-/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }
}

export default Utils;
